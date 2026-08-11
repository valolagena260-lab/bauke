import os
import threading
import asyncio
import re
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ডামি ওয়েব সার্ভার ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Menu Bot is successfully running on Render!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- বটের মূল কোড ---
TOKEN = os.environ.get("BOT_TOKEN")

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
    await update.message.reply_text("হ্যালো! আমি গ্রুপের স্ক্যাম লিংক রিমুভ করি। আমার মেনু দেখতে চাইলে 'my go' বা 'mygo' লিখে মেসেজ দিন।")

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
        # --- ২. "mygo" বা "my go" চেক করে বাটন মেনু দেওয়া ---
        text_lower = text_to_check.lower()
        if "mygo" in text_lower or "my go" in text_lower:
            # বাটনের লিস্ট তৈরি
            keyboard = [
                [InlineKeyboardButton("📺 MY TV সম্পর্কে জানুন", callback_data="about_mytv")],
                [InlineKeyboardButton("🔗 লাইভ লিংক", callback_data="live_link")],
                [InlineKeyboardButton("📞 অ্যাডমিনের সাথে যোগাযোগ", callback_data="contact_admin")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text(
                "হ্যালো! আপনি MY TV সম্পর্কে কী জানতে চান? নিচের লিস্ট থেকে ক্লিক করুন:",
                reply_markup=reply_markup
            )

# --- ৩. বাটনে ক্লিক করলে যে রিপ্লাই দেবে ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # টেলিগ্রামকে জানানো যে ক্লিক রিসিভ হয়েছে

    data = query.data
    
    # স্ক্রিপ্টে লেখা নির্দিষ্ট উত্তর
    if data == "about_mytv":
        text = "MY TV হলো একটি দারুণ এন্টারটেইনমেন্ট প্ল্যাটফর্ম। এখানে আপনি বিভিন্ন কনটেন্ট উপভোগ করতে পারবেন।"
    elif data == "live_link":
        text = "MY TV লাইভ দেখার লিংক: https://mytb.fun\nএছাড়াও আপনি আমাদের .m3u প্লেলিস্ট ব্যবহার করতে পারেন।"
    elif data == "contact_admin":
        text = "যেকোনো দরকারে বা সমস্যার জন্য আমাদের অ্যাডমিনের সাথে ইনবক্সে যোগাযোগ করুন।"
    else:
        text = "দুঃখিত, কোনো তথ্য পাওয়া যায়নি।"

    # উত্তরটি নতুন মেসেজ হিসেবে সেন্ড করবে
    await query.message.reply_text(text)

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN পাওয়া যায়নি!")
        return
    
    threading.Thread(target=run_web, daemon=True).start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    
    # হ্যান্ডলার যুক্ত করা
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_message))
    app.add_handler(CallbackQueryHandler(button_click)) # বাটন ক্লিকের হ্যান্ডলার

    print("বাটন মেনু বট চালু হয়েছে...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
