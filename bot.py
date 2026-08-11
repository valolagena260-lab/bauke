
import os
import threading
import asyncio
import re
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- ডামি ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is successfully running on Render!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- বটের মূল কোড ---
TOKEN = os.environ.get("BOT_TOKEN")

LINK_REGEX = r"(https?://\S+|www\.\S+|t\.me/\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?)"

ALLOWED_EXTENSIONS = [".m3u", ".mpd", ".m3u8"]
ALLOWED_SITES = ["mytb.fun"]

# --- বটের পরিচয় জানতে চাওয়ার কিওয়ার্ড ---
IDENTITY_KEYWORDS = ["তুমি কে", "tumi ke", "who are you", "bot ke", "বট কে", "apni ke", "আপনি কে", "who is this"]

def is_allowed_link(link: str) -> bool:
    link_lower = link.lower()
    base_link = link_lower.split("?")[0]
    for ext in ALLOWED_EXTENSIONS:
        if base_link.endswith(ext):
            return True
    for site in ALLOWED_SITES:
        if site in link_lower:
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমি MY TV এর অ্যাসিস্ট্যান্ট এবং গ্রুপের স্ক্যাম লিংক রিমুভ করতে প্রস্তুত। 🚀")

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # গ্রুপ বা সুপারগ্রুপ ছাড়া কাজ করবে না
    if message.chat.type not in ['group', 'supergroup']:
        return

    should_delete = False
    text_to_check = message.text or message.caption or ""

    # ১. চেক করা: মেসেজটি কি ফরওয়ার্ড করা?
    if message.forward_origin:
        should_delete = True
        
    # ২. চেক করা: মেসেজে কোনো লিংক আছে কি না
    elif text_to_check:
        links = re.findall(LINK_REGEX, text_to_check)
        for link in links:
            if not is_allowed_link(link):
                should_delete = True
                break

    # ডিলিট করার কারণ থাকলে ডিলিট করবে
    if should_delete:
        try:
            await message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
    else:
        # --- যদি মেসেজটি ডিলিট না হয়, তবে চেক করবে কেউ বটের পরিচয় জানতে চাইছে কি না ---
        if text_to_check:
            text_lower = text_to_check.lower()
            # যদি কিওয়ার্ডগুলোর কোনো একটি মেসেজের মধ্যে থাকে
            if any(keyword in text_lower for keyword in IDENTITY_KEYWORDS):
                await message.reply_text("আমি MY TV এর অ্যাসিস্ট্যান্ট। MY TV সম্পর্কে কিছু জানতে চাইলে আমাকে জিজ্ঞাসা করতে পারেন।")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN পাওয়া যায়নি! Render-এ Environment Variable চেক করুন।")
        return

    threading.Thread(target=run_web, daemon=True).start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_message))

    print("অ্যান্টি-লিংক এবং অটো-রিপ্লাই বট চালু হয়েছে...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
