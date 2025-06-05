import os
import nest_asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

nest_asyncio.apply()

TOKEN = os.environ["TOKEN"]
keyword = "hello"
waiting_for_keyword = set()

app = FastAPI()
bot_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Bot is active. Current keyword: \"{keyword}\"')

async def set_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global keyword, waiting_for_keyword
    if context.args:
        keyword = ' '.join(context.args)
        await update.message.reply_text(f'Keyword updated to: \"{keyword}\"')
    else:
        waiting_for_keyword.add(update.message.from_user.id)
        await update.message.reply_text('Please send the new keyword as your next message.')

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global keyword, waiting_for_keyword
    user_id = update.message.from_user.id
    if user_id in waiting_for_keyword:
        keyword = update.message.text
        waiting_for_keyword.remove(user_id)
        await update.message.reply_text(f'Keyword updated to: \"{keyword}\"')
        return
    if keyword.lower() in update.message.text.lower():
        await update.message.reply_text(f'Keyword \"{keyword}\" detected in your message!')

@app.on_event("startup")
async def on_startup():
    global bot_app
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler('start', start))
    bot_app.add_handler(CommandHandler('setkeyword', set_keyword))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    # Application needs to be initialized and started for webhook to work
    await bot_app.initialize()
    await bot_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    global bot_app
    await bot_app.stop()
    await bot_app.shutdown()

@app.post(f"/{TOKEN}/")
async def webhook(request: Request):
    global bot_app
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}
