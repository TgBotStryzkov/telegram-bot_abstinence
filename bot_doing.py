from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import datetime
import asyncio
import os
import random
import json
import requests
import re
from telegram.ext import Application
import time
import nest_asyncio
nest_asyncio.apply()

# 🔒 Глобальный кэш пользователей
user_cache = {}

# 🔑 Пул ключей Groq API
groq_keys = [
    "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",
    "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",
    "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"
]

# 🔢 Индекс текущего ключа
groq_key_index = 0

# ✅ Загрузка данных пользователя
def load_user_json(user_id):
    if user_id in user_cache:
        return user_cache[user_id]
    filepath = f"user_data/{user_id}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "start_date": str(datetime.date.today()),
            "reports": [],
            "username": None
        }
    user_cache[user_id] = data
    return data






# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Добро пожаловать! Напиши отчёт или выбери функцию.")

# Команда /support
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✉️ Напиши разработчикам: @Mihailstryzkov")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>🛠 Доступные команды:</b>\n\n"
        "/start — Запустить бота\n"
        "/support — Связь с разработчиками\n"
        "/help — Показать это меню\n"
        "● день — Посмотреть текущий день\n"
        "● отчёт — Отправить ежедневный отчёт\n"
        "● история — Посмотреть последние отчёты\n"
        "● наставник — Вопрос к ИИ-наставнику\n\n"
        "💡 Просто напиши ключевое слово, и бот ответит!"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')






# 📂 Загрузка всех сообщений братства
def load_bro_messages():
    path = "bro_messages.json"
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except json.JSONDecodeError:
        print("⚠️ Ошибка при чтении bro_messages.json")
        return []

# 💾 Сохранение нового сообщения братства
def save_bro_message(text: str):
    messages = load_bro_messages()
    messages.append(text)
    with open("bro_messages.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# 💾 Сохранение данных одного пользователя
def save_user_json(user_id: int, data: dict):
    user_cache[user_id] = data  # обновляем кэш
    os.makedirs("user_data", exist_ok=True)  # создаём папку при необходимости
    filepath = f"user_data/{user_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 💾 Автоматическое сохранение всех пользователей из кэша
def autosave_all_users():
    for user_id, data in user_cache.items():
        save_user_json(user_id, data)
    print("✅ Все данные пользователей автоматически сохранены.")







# 📲 Команда /start — приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username  # ← Никнейм пользователя

    # Загружаем данные пользователя
    data = load_user_json(user_id)

    # Обновляем username, если он появился или изменился
    if username and data.get("username") != username:
        data["username"] = username
        save_user_json(user_id, data)

    # Кэшируем в памяти
    user_cache[user_id] = data  # 👈 исправлено: user_data → user_cache

    # Клавиатура
    keyboard = [
        ["День", "Сброс"],
        ["Отчёт", "История"],
        ["Сорваться хочу", "Письмо брату"]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"👊 Привет, @{username if username else 'друг'}! Я твой антислив-бот. Нажми кнопку или напиши вручную.",
        reply_markup=markup
    )

# 💬 Рандомные фразы поддержки
support_phrases = [
    "🛑 Сделай паузу. Дыши. Ты не обязан сливаться.",
    "🔥 Импульс — это волна. Пережди. Ты сильнее.",
    "💪 Переключись: 10 отжиманий, холодная вода, выход на улицу.",
    "🧠 Срыв не даёт ничего, кроме вины. Победа — даёт силу.",
    "🎯 Ты уже на пути. Каждый день — как меч в ножнах. Не выбрасывай его.",
    "🚿 Прими душ. Прогуляйся. Напиши мне отчёт вместо слива.",
    "🔁 Не возвращайся туда, откуда так тяжело вылезал.",
    "🛑 Стоп. Ты на грани, и это нормально.\n\n🔹 Сделай 5 глубоких вдохов\n🔹 20 приседаний или 10 отжиманий\n🔹 Выпей воды и выйди на улицу\n\nТы сильнее этого импульса. Я с тобой. Не сдавайся 💪"
]








# 🗣 Обработка обычных текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().lower()
    user_id = update.effective_user.id

    # Загрузка данных пользователя
    data = load_user_json(user_id)

    # Команда: День
    if msg == "день":
        start = datetime.date.fromisoformat(data["start_date"])
        days = (datetime.date.today() - start).days
        await update.message.reply_text(f"📅 Ты уже держишься {days} дней!")

    # Команда: Сброс
    elif msg == "сброс":
        data["start_date"] = str(datetime.date.today())
        save_user_json(user_id, data)
        await update.message.reply_text("🔁 День обнулён. Начни с новой силы!")

    # Команда: Отчёт
    elif msg == "отчёт":
        await update.message.reply_text("📝 Напиши свой отчёт за сегодня. Я запишу.")
        context.user_data["awaiting_report"] = True

    # Пользователь пишет отчёт
    elif context.user_data.get("awaiting_report"):
        today = str(datetime.date.today())
        report_text = update.message.text.strip()

        # Проверка длины
        if len(report_text) > 333:
            await update.message.reply_text("❗️Слишком длинный отчёт. Максимум — 333 символа.")
            return

        # Сохраняем отчёт
        data.setdefault("reports", []).append(f"{today}: {report_text}")
        save_user_json(user_id, data)

        await update.message.reply_text("✅ Я записал твой отчёт. Горд тобой.")
        context.user_data["awaiting_report"] = False








    elif msg == "история":
        data = load_user_json(user_id)
        reports = data.get("reports", [])

        if reports:
            last = reports[-3:] if len(reports) > 3 else reports

            formatted = []
            for r in last:
                if isinstance(r, dict):
                    text = f"📅 {r.get('дата', '???')} — {r.get('отчёт', 'Без текста')}"
                else:
                    text = str(r)  # просто текст, если это не словарь
                formatted.append(text)

            reply_text = "📜 Последние отчёты:\n\n" + "\n".join(formatted)
            await update.message.reply_text(reply_text)
        else:
            await update.message.reply_text("❌ У тебя пока нет ни одного отчёта.")

    elif msg == "сорваться хочу":
        support = random.choice(support_phrases)  # выбираем мотивационную фразу
        bros = load_bro_messages()  # загружаем письма от других пользователей
        letter = f"\n\n📨 Письмо от брата:\n“{random.choice(bros)}”" if bros else ""  # добавляем, если письма есть
        await update.message.reply_text(support + letter)

    elif msg == "письмо брату":
        await update.message.reply_text(
            "💌 Напиши короткое послание поддержки для другого мужчины. Оно будет анонимно отправлено в трудный момент."
        )
        context.user_data["writing_bro_letter"] = True

    elif context.user_data.get("writing_bro_letter"):
        save_bro_message(update.message.text)
        await update.message.reply_text(
            "✅ Твоё письмо сохранено. Оно обязательно поддержит кого-то в трудный момент. Спасибо 🙏")
        context.user_data["writing_bro_letter"] = False








    else:
        # Загрузка данных пользователя
        data = load_user_json(user_id)
        last_time = data.get("last_ai_request")
        now = time.time()

        # ⏳ Ограничение: не чаще одного запроса в 10 секунд
        if last_time and now - last_time < 10:
            wait = int(10 - (now - last_time))
            await update.message.reply_text(f"⏳ Подожди ещё {wait} сек перед следующим вопросом.")
            return

        await update.message.reply_text("🤖 Думаю...")

        try:
            # 🔐 Получение текущего ключа Groq
            global groq_key_index
            current_key = groq_keys[groq_key_index]
            groq_key_index = (groq_key_index + 1) % len(groq_keys)

            headers = {
                "Authorization": f"Bearer {current_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты опытный наставник для мужчин. Общайся как Дэвид Гоггинс — строго, мужественно, по делу. "
                            "Отвечай исключительно по-русски. Не используй иностранные слова, латиницу, арабские или китайские символы. "
                            "Пиши только кириллицей, с цифрами и знаками препинания. "
                            "Говори грамотно, соблюдая окончания слов и падежи. Всегда завершай мысль полностью — не обрывай предложения. "
                            "Слова вроде 'что-то', 'где-то', 'когда-то', 'кто-то' всегда пиши через дефис. Никогда не пиши 'чтото', 'гдето'. "
                            "Никогда не ставь точку сразу после союза."
                        )
                    },
                    {"role": "user", "content": "Напиши пример, где используются слова типа что-то и где-то."},
                    {"role": "assistant",
                     "content": "Когда ты решаешь **что-то** важное, подумай, **где-то** в прошлом ты уже сталкивался с этим."},
                    {"role": "user",
                     "content": "Напиши строго, мужественно. Используй слова типа что-то, где-то. Не обрывай предложение."},
                    {"role": "assistant",
                     "content": "Ты должен решить **что-то** важное, брат. **Где-то** внутри ты знаешь, что делать. Не останавливайся."},
                    {"role": "user", "content": msg}
                ]
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]

            # ✂️ Ограничим длину, завершив по знаку препинания
            max_chars = 900
            if len(reply) > max_chars:
                end = max(
                    reply.rfind(".", 0, max_chars),
                    reply.rfind("?", 0, max_chars),
                    reply.rfind("!", 0, max_chars)
                )
                reply = reply[:end + 1] if end != -1 else reply[:max_chars]

            # 🧼 Очистка от нежелательных символов
            reply = re.sub(r'[a-zA-Z]', '', reply)
            reply = re.sub(r'[⺀-鿿一-龯ぁ-ゔァ-ヴー々〆〤]', '', reply)
            reply = re.sub(r'[^\u0400-\u04FF0-9.,!?—–\s\n]', '', reply)
            reply = re.sub(r'\s{2,}', ' ', reply).strip()

            # 💾 Сохраняем время последнего обращения
            data["last_ai_request"] = now
            save_user_json(user_id, data)

            await update.message.reply_text(reply)

        except Exception as e:
            await update.message.reply_text("❌ Ошибка при обращении к Groq API.")
            print("Ошибка:", e)









# ⏰ Утреннее напоминание
async def morning_message(app: Application) -> None:
    for user_id, data in user_cache.items():
        try:
            start_date = datetime.date.fromisoformat(data["start_date"])
            days = (datetime.date.today() - start_date).days
            await app.bot.send_message(
                chat_id=user_id,
                text=f"🌅 Доброе утро! День {days}. Ты в игре. Не сдавайся 💪"
            )
        except Exception as e:
            print(f"Ошибка при отправке утреннего сообщения пользователю {user_id}: {e}")

# 🌙 Вечернее напоминание
async def evening_message(app: Application) -> None:
    for user_id in user_cache:
        try:
            await app.bot.send_message(
                chat_id=user_id,
                text="🌙 Время подвести итоги. Напиши отчёт, даже если день был тяжёлым. Ты растёшь!"
            )
        except Exception as e:
            print(f"Ошибка при отправке вечернего сообщения пользователю {user_id}: {e}")







# Предполагается, что у тебя уже есть эти импорты и функции:
# from your_module import start, help_command, support, handle_text, morning_message, evening_message, autosave_all_users

async def main():
    # Создание приложения
    app = ApplicationBuilder().token("8164293392:AAEJU4G3OLHydRiv6pmh9RboxrK50_X7TPc").build()

    # Установка автоподсказок команд
    await app.bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("support", "Написать разработчикам"),
        BotCommand("help", "Список доступных функций")
    ])

    # Удаление webhook (если был установлен)
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Хендлеры команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("support", support))

    # Хендлер для обычных сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Планировщик задач (утро, вечер, автосохранение)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(morning_message, CronTrigger(hour=9, minute=0), args=[app])
    scheduler.add_job(evening_message, CronTrigger(hour=21, minute=0), args=[app])
    scheduler.add_job(autosave_all_users, CronTrigger(minute="*/3"))
    scheduler.start()

    # Запуск polling'а (асинхронный режим)
    await app.run_polling()

# Точка входа
if __name__ == "__main__":
    asyncio.run(main())
