from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import BotCommand
import datetime
import asyncio
import os
import random
import json
import requests
import re
import nest_asyncio
nest_asyncio.apply()


user_cache = {}  # глобальный кэш в оперативной памяти

# 🗝️ Пул Groq API ключей
groq_keys = [
    "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",
    "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",
    "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"
]

# 🔢 Индекс текущего ключа
groq_key_index = 0



def load_user_json(user_id):
    if user_id in user_cache:
        return user_cache[user_id]
    filepath = f"user_data/{user_id}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"start_date": str(datetime.date.today()), "reports": [], "username": None}
    user_cache[user_id] = data
    return data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Добро пожаловать! Напиши отчёт или выбери функцию.")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✉️ Напиши разработчикам: @Mihailstryzkov")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Доступные команды:\n"
        "/start — Запустить бота\n"
        "/support — Связь с разработчиками\n"
        "/help — Показать это меню"
    )

    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — Начать работу с ботом\n"
        "/help — Справка по функциям бота\n"
        "● день — Посмотреть текущий день\n"
        "● отчёт — Отправить ежедневный отчёт\n"
        "● история — Посмотреть последние отчёты\n"
        "● наставник — Вопрос к ИИ-наставнику\n\n"
        "💡 Просто напиши ключевое слово, и бот ответит!"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     help_text = (
#         "📋 <b>Доступные команды:</b>\n\n"
#         "/start — Начать работу с ботом\n"
#         "/help — Справка по функциям бота\n"
#         "● день — Посмотреть текущий день\n"
#         "● отчёт — Отправить ежедневный отчёт\n"
#         "● история — Посмотреть последние отчёты\n"
#         "● наставник — Вопрос к ИИ-наставнику\n\n"
#         "💡 Просто напиши ключевое слово, и бот ответит!"
#     )
#     await update.message.reply_text(help_text, parse_mode='HTML')

def load_bro_messages():
    path = "bro_messages.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except json.JSONDecodeError:
            return []
    return []

def save_bro_message(text):
    messages = load_bro_messages()
    messages.append(text)
    with open("bro_messages.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def autosave_all_users():
    for user_id, data in user_cache.items():
        save_user_json(user_id, data)
    print("✅ Все данные пользователей автоматически сохранены.")

def save_user_json(user_id, data):
    user_cache[user_id] = data  # обновляем кэш
    filepath = f"user_data/{user_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Память
user_data = {}

# Приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.effective_user.username  # ← Получаем никнейм пользователя

    # Загружаем текущие данные
    data = load_user_json(user_id)

    # Если у пользователя появился или изменился username — обновим
    if username and data.get("username") != username:
        data["username"] = username
        save_user_json(user_id, data)

    user_data[user_id] = data  # сохраняем в оперативную память

    keyboard = [["День", "Сброс"], ["Отчёт", "История"], ["Сорваться хочу", "Письмо брату"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"👊 Привет, @{username if username else 'друг'}! Я твой антислив-бот. Нажми кнопку или напиши вручную.",
        reply_markup=markup
    )

#РАНДОМНЫЕ ФРАЗЫ
support_phrases = [
    "🛑 Сделай паузу. Дыши. Ты не обязан сливаться.",
    "🔥 Импульс — это волна. Пережди. Ты сильнее.",
    "💪 Переключись: 10 отжиманий, холодная вода, выход на улицу.",
    "🧠 Срыв не даёт ничего, кроме вины. Победа — даёт силу.",
    "🎯 Ты уже на пути. Каждый день — как меч в ножнах. Не выбрасывай его.",
    "🚿 Прими душ. Прогуляйся. Напиши мне отчёт вместо слива.",
    "🔁 Не возвращайся туда, откуда так тяжело вылезал.",
    "🛑 Стоп. Ты на грани, и это нормально.\n\n 🔹 Сделай 5 глубоких вдохов\n 🔹 20 приседаний или 10 отжиманий\n 🔹 Выпей воды и выйди на улицу\n\n Ты сильнее этого импульса. Я с тобой. Не сдавайся 💪"
]

# Ответ на обычный текст
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().lower()
    user_id = update.effective_user.id

    if msg == "день":
        data = load_user_json(user_id)
        start = datetime.date.fromisoformat(data["start_date"])
        days = (datetime.date.today() - start).days
        await update.message.reply_text(f"📅 Ты уже держишься {days} дней!")

    elif msg == "сброс":
        data = load_user_json(user_id)  # загрузили данные из кэша/файла
        data["start_date"] = str(datetime.date.today())  # обновили дату
        save_user_json(user_id, data)  # сохранили назад
        await update.message.reply_text("🔁 День обнулён. Начни с новой силы!")

    elif msg == "отчёт":
        await update.message.reply_text("📝 Напиши свой отчёт за сегодня. Я запишу.")
        context.user_data["awaiting_report"] = True

    elif context.user_data.get("awaiting_report"):
        data = load_user_json(user_id)
        today = str(datetime.date.today())

        # Проверка: длина текста
        if len(update.message.text) > 333:
            await update.message.reply_text("❗️Слишком длинный отчёт. Максимум — 333 символов.")
            return

        # # Проверка: был ли уже отчёт сегодня
        # if any(report["date"] == today for report in data.get("reports", [])):
        #     await update.message.reply_text("📌 Ты уже писал отчёт сегодня. Молодец!")
        #     context.user_data["awaiting_report"] = False
        #     return

        # Добавление нового отчёта
        report_text = f"{today}: {update.message.text}"
        data.setdefault("reports", []).append(report_text)
        save_user_json(user_id, data)

        await update.message.reply_text("✅ Я записал твой отчёт. Горд тобой.")
        context.user_data["awaiting_report"] = False

    elif msg == "история":
        data = load_user_json(user_id)  # загружаем данные из кэша или файла
        reports = data.get("reports", [])  # список отчётов (может быть пустым)

        if reports:
            last = reports[-3:] if len(reports) > 3 else reports
            reply_text = "📜 Последние отчёты:\n\n" + "\n".join(last)
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
        # ЗАГРУЖАЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
        data = load_user_json(user_id)
        import time
        last_time = data.get("last_ai_request")
        now = time.time()

        # ЕСЛИ ПРОШЛО МЕНЬШЕ 30 СЕКУНД — ОТКАЗ
        if last_time and now - last_time < 10:
            wait = int(10 - (now - last_time))
            await update.message.reply_text(f"⏳ Подожди ещё {wait} сек перед следующим вопросом.")
            return

        # ⬇️ Вот здесь — только если всё ок, тогда пишем «Думаю...»
        await update.message.reply_text("🤖 Думаю...")

        global groq_key_index  # Используем глобальную переменную
        # Получаем текущий ключ
        current_key = groq_keys[groq_key_index]
        # Увеличиваем индекс, а если дошли до конца — начинаем сначала
        groq_key_index = (groq_key_index + 1) % len(groq_keys)
        headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json"
        }
        data_request = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "Ты опытный наставник для мужчин. Общайся как Дэвид Гоггинс — строго, мужественно, по делу. Отвечай исключительно по-русски. Не используй иностранные слова, латиницу, арабские или китайские символы. Пиши только кириллицей, с цифрами и знаками препинания. Говори грамотно, соблюдая окончания слов и падежи. Всегда завершай мысль полностью — не обрывай предложения. Слова вроде 'что-то', 'где-то', 'когда-то', 'кто-то' всегда пиши через дефис, иначе это ошибка. Никогда не пиши 'чтото', 'гдето'. Следи за орфографией и пунктуацией. Никогда не пиши частицу 'то' слитно со словами — всегда используй дефис: 'что-то', 'где-то', 'когда-то'. Следи за пунктуацией — никогда не ставь точку сразу после союза. Всегда завершай мысль полностью."},

                {"role": "user", "content": "Напиши пример, где используются слова типа что-то и где-то."},
                {"role": "assistant", "content": "Когда ты решаешь **что-то** важное, постарайся подумать о том, **где-то** в прошлом ты уже сталкивался с подобным. Слова типа \"что-то\", \"где-то\" и \"когда-то\" пишутся через дефис."},

                {"role": "user", "content": "Напиши строго, мужественно. Используй слова типа что-то, где-то. Не обрывай предложение."},
                {"role": "assistant", "content": "Ты должен решить, что-то важное, брат. Где-то внутри ты знаешь, что делать. Но не останавливайся — продолжай двигаться вперёд."},


                {"role": "user", "content": msg}
            ]

        }

        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data_request)
            reply = response.json()["choices"][0]["message"]["content"]

            # Ограничение по длине с учётом смысла
            max_chars = 900
            if len(reply) > max_chars:
                end = max(reply.rfind(".", 0, max_chars),
                          reply.rfind("?", 0, max_chars),
                          reply.rfind("!", 0, max_chars))
                if end != -1:
                    reply = reply[:end + 1]
                else:
                    reply = reply[:max_chars]

            # Очистка от латиницы и азиатских символов
            reply = re.sub(r'[a-zA-Z]', '', reply)  # латиница
            reply = re.sub(r'[一-龯ぁ-ゔァ-ヴー々〆〤]', '', reply)  # японский
            reply = re.sub(r'[⺀-鿿]', '', reply)  # китайский
            reply = re.sub(r'[^\w\s.,!?—–-]', '', reply)  # всё остальное мусорное
            # Очистка от латиницы, арабских, китайских и прочих символов
            reply = re.sub(r'[^\u0400-\u04FF0-9.,!?—–\s\n]', '', reply)
            reply = re.sub(r'\s{2,}', ' ', reply)  # убирает лишние пробелы
            reply = reply.strip()  # убирает пробелы в начале и конце

            # 💾 СОХРАНЯЕМ ВРЕМЯ ЗАПРОСА
            data["last_ai_request"] = time.time()
            save_user_json(user_id, data)
            # Отправка пользователю
            await update.message.reply_text(reply)

        except Exception as e:
            await update.message.reply_text("❌ Ошибка при обращении к Groq API: " + str(e))

#напоминания утром и вечером
async def morning_message(app):
    for user_id in user_data:
        start = user_data[user_id]["start_date"]
        days = (datetime.date.today() - start).days
        await app.bot.send_message(
            chat_id=user_id,
            text=f"🌅 Доброе утро! День {days}. Ты в игре. Не сдавайся 💪"
        )

async def evening_message(app):
    for user_id in user_data:
        await app.bot.send_message(
            chat_id=user_id,
            text="🌙 Время подвести итоги. Напиши отчёт, даже если день был тяжёлым. Ты растёшь!"
        )








# Запуск бота
async def main():
    app = ApplicationBuilder().token("8164293392:AAEJU4G3OLHydRiv6pmh9RboxrK50_X7TPc").build()

    # Установка автоподсказок команд
    await app.bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("support", "Написать разработчикам"),
        BotCommand("help", "Список доступных функций")
    ])

    # Отключаем webhook
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Обработчики команд и сообщений
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    # ⏰ создаём и запускаем планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(morning_message, CronTrigger(hour=9, minute=00), args=[app])
    scheduler.add_job(evening_message, CronTrigger(hour=21, minute=0), args=[app])
    scheduler.add_job(autosave_all_users, CronTrigger(minute="*/3"))
    scheduler.start()

    # Запускаем бота (это асинхронный polling)
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
