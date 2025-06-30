import asyncio
from telegram.ext import Application, CommandHandler

async def start(update, context):
    await update.message.reply_text("Привет! Я работаю!")

def main():
    app = Application.builder().token("ТВОЙ_ТОКЕН").build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
