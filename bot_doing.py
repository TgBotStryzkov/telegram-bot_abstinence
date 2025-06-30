import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

async def start(update, context):
    await update.message.reply_text("Привет! Я антислив-бот.")

async def main():
    app = ApplicationBuilder().token("8164293392:AAEJU4G3OLHydRiv6pmh9RboxrK50_X7TPc").build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
