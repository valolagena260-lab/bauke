import os
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- ডামি ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is successfully running on Render!"

def run_web():
    # Render সাধারণত 10000 পোর্টে রান করে
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- বটের মূল কোড ---
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমি একটি টেলিগ্রাম বট। Render.com-এর ফ্রি Web Service থেকে চলছি! 🚀")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"আপনি বলেছেন: {user_text}")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN পাওয়া যায়নি! Render-এ Environment Variable চেক করুন।")
        return

    # ওয়েব সার্ভারটিকে ব্যাকগ্রাউন্ডে চালু করা
    threading.Thread(target=run_web, daemon=True).start()

    # --- এরর ফিক্স: নতুন Asyncio Event Loop তৈরি করা ---
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # বটের অ্যাপ্লিকেশন তৈরি
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("বট চালু হয়েছে...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
