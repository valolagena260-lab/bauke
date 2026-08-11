import os
import threading
import asyncio
import re
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ডামি ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Advanced Group Bot is running on Render!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- বটের মূল ভ্যারিয়েবল ---
TOKEN = os.environ.get("BOT_TOKEN")
JSON_URL = "https://raw.githubusercontent.com/valolagena260-lab/bauke/refs/heads/main/data.json"
CHANNEL_USERNAME = "@msmofworld" # <-- এখানে আপনার চ্যানেলের ইউজারনেম দিন

LINK_REGEX = r"(https?://\S+|www\.\S+|t\.me/\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?)"
ALLOWED_EXTENSIONS = [".m3u", ".mpd", ".m3u8"]
ALLOWED_SITES = ["mytb.fun"]

# JSON ডাটা আনার ফাংশন
def get_json_data():
    try:
        response = requests.get(JSON_URL)
        return response.json()
    except Exception as e:
        print("Error fetching JSON:", e)
        return None

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

# --- ওয়েলকাম মেসেজ এবং চ্যানেল জয়েন চেক ---
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        # বট জয়েন করলে তাকে মেসেজ দেবে না
        if new_member.is_bot:
            continue
            
        try:
            # চেক করা ইউজার চ্যানেলে আছে কিনা
            member_status = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=new_member.id)
            if member_status.status in ['member', 'administrator', 'creator']:
                # চ্যানেলে থাকলে শুধু ওয়েলকাম মেসেজ
                await update.message.reply_text(f"স্বাগতম {new_member.first_name}! আমাদের গ্রুপে আপনাকে পেয়ে আমরা আনন্দিত। 🎉")
            else:
                # চ্যানেলে না থাকলে ওয়েলকাম মেসেজ + জয়েন বাটন
                keyboard = [[InlineKeyboardButton("📢 আমাদের চ্যানেলে জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"স্বাগতম {new_member.first_name}! সব আপডেট পেতে দয়া করে আমাদের অফিশিয়াল চ্যানেলে জয়েন করুন।",
                    reply_markup=reply_markup
                )
        except Exception as e:
            print("Channel checking error:", e)
            await update.message.reply_text(f"স্বাগতম {new_member.first_name}! 🎉")

# --- ৫ মিনিট পর বাটন ডিলিট করার ফাংশন ---
async def remove_button_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    message_id = job.data
    try:
        # বাটন রিমুভ করে দেওয়া
        await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception as e:
        pass # যদি ক্লিক করে আগেই বাটন রিমুভ করে দেয়, তবে এই এরর ইগনোর করবে

# --- রেগুলার মেসেজ চেক ---
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    should_delete = False
    text_to_check = message.text or message.caption or ""

    if not text_to_check:
        return

    # ১. স্ক্যাম লিংক ও ফরওয়ার্ড রিমুভ করা
    if message.chat.type in ['group', 'supergroup']:
        if message.forward_origin:
            should_delete = True
        else:
            links = re.findall(LINK_REGEX, text_to_check)
            for link in links:
                if not is_allowed_link(link):
                    should_delete = True
                    break

    if should_delete:
        try:
            await message.delete()
        except Exception as e:
            print("Error deleting message:", e)
    else:
        # ২. "mygo" বা "my go" চেক করে JSON থেকে বাটন মেনু দেওয়া
        text_lower = text_to_check.lower()
        if "mygo" in text_lower or "my go" in text_lower:
            data = get_json_data()
            if not data:
                await message.reply_text("দুঃখিত, সার্ভার থেকে ডাটা আনা যাচ্ছে না।")
                return
            
            menu_text = data.get("menu_text", "মেনু:")
            buttons_data = data.get("buttons", [])
            
            # JSON এর বাটন দিয়ে কীবোর্ড তৈরি করা
            keyboard = []
            for btn in buttons_data:
                keyboard.append([InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"])])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_msg = await message.reply_text(menu_text, reply_markup=reply_markup)
            
            # ৫ মিনিট (300 সেকেন্ড) পর বাটন রিমুভ করার টাইমার চালু করা
            context.job_queue.run_once(remove_button_job, 300, chat_id=message.chat_id, data=sent_msg.message_id)

# --- বাটনে ক্লিক করার পর আনসার দেওয়া ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_key = query.data
    json_data = get_json_data()
    
    reply_text = "দুঃখিত, তথ্য পাওয়া যায়নি।"
    if json_data and "answers" in json_data:
        reply_text = json_data["answers"].get(data_key, reply_text)

    # ক্লিক করার সাথে সাথে বাটনটি রিমুভ করে দেওয়া
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except:
        pass
        
    # উত্তর পাঠানো
    await query.message.reply_text(reply_text)

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN পাওয়া যায়নি!")
        return
    
    threading.Thread(target=run_web, daemon=True).start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    
    # নতুন মেম্বার আসার হ্যান্ডলার
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.NEW_CHAT_MEMBERS, check_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("অ্যাডভান্সড বট চালু হয়েছে...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
