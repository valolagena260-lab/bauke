import os
import threading
import asyncio
import re
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# --- ডামি ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "AI Bot is successfully running on Render!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- বটের মূল কোড ---
TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- নতুন Gemini AI সেটআপ ---
ai_client = None
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

LINK_REGEX = r"(https?://\S+|www\.\S+|t\.me/\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?)"
ALLOWED_EXTENSIONS = [".m3u", ".mpd", ".m3u8"]
ALLOWED_SITES = ["mytb.fun"]

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
    await update.message.reply_text("হ্যালো! আমি MY TV এর এআই (AI) অ্যাসিস্ট্যান্ট। আমাকে যেকোনো কিছু জিজ্ঞাসা করতে পারেন! 🚀")

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    should_delete = False
    text_to_check = message.text or message.caption or ""

    if not text_to_check:
        return

    # --- ১. গ্রুপের জন্য স্ক্যাম লিংক ও ফরওয়ার্ড চেক ---
    if message.chat.type in ['group', 'supergroup']:
        if message.forward_origin:
            should_delete = True
        else:
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
        # --- ২. AI দিয়ে অটো-রিপ্লাই ---
        if ai_client:
            await context.bot.send_chat_action(chat_id=message.chat_id, action='typing')
            try:
                # নতুন গুগলের সিস্টেমে উত্তর জেনারেট করা
                response = await ai_client.aio.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=text_to_check,
                    config=types.GenerateContentConfig(
                        system_instruction="তুমি হলে 'MY TV' এর একজন স্মার্ট অ্যাসিস্ট্যান্ট। তোমার কাজ হলো ইউজারদের সাহায্য করা। কেউ যেকোনো ভাষায় প্রশ্ন করলে তুমি নিজে থেকে বুঝে সুন্দর করে বাংলায় উত্তর দেবে।"
                    )
                )
                await message.reply_text(response.text)
            except Exception as e:
                print(f"AI Error: {e}")
                await message.reply_text("দুঃখিত, আমার সার্ভারে একটু সমস্যা হচ্ছে। একটু পর আবার চেষ্টা করুন।")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN পাওয়া যায়নি!")
        return
    
    threading.Thread(target=run_web, daemon=True).start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_message))

    print("AI অ্যাসিস্ট্যান্ট বট চালু হয়েছে...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
