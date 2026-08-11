import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Render-এর Environment Variable থেকে টোকেন নেওয়ার জন্য
TOKEN = os.environ.get("BOT_TOKEN")

# /start কমান্ড দিলে এই মেসেজটি আসবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমি একটি টেলিগ্রাম বট। Render.com থেকে সফলভাবে চলছি! 🚀")

# কেউ কোনো টেক্সট মেসেজ দিলে বট সেটিই রিপ্লাই করবে (Echo Bot)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"আপনি বলেছেন: {user_text}")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN পাওয়া যায়নি! Render-এ Environment Variable চেক করুন।")
        return

    # বটের অ্যাপ্লিকেশন তৈরি
    app = Application.builder().token(TOKEN).build()

    # হ্যান্ডলার যুক্ত করা
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("বট চালু হয়েছে...")
    
    # বট রান করা
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
