import os
import threading
import asyncio
import re
import requests
import json
from flask import Flask, render_template, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import MessageEntityType

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "MY TV Earn Bot & Web App is running!"

@web_app.route('/earn')
def earn_page():
    return render_template('earn.html')

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

TOKEN = os.environ.get("BOT_TOKEN")
JSON_URL = "https://raw.githubusercontent.com/valolagena260-lab/bauke/refs/heads/main/data.json"

CHANNEL_USERNAME = "@msmofworld" 
GROUP_CHAT_ID = -1002190441261 
ADMIN_CHAT_ID = 7477535984 

LINK_REGEX = r"(https?://\S+|www\.\S+|t\.me/\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?)"
MENTION_REGEX = r"@[a-zA-Z0-9_]{5,32}" 
ALLOWED_EXTENSIONS = [".m3u", ".mpd", ".m3u8"]
ALLOWED_SITES = ["mytb.fun"]

SPAM_KEYWORDS = [
    "caught on tape", "cheated on husband", "leaked", "vip vault", 
    "uncensored", "hot video", "private tape", "private link", 
    "play video", "open private", "secret vault", "18+"
]

RECHARGE_KEYWORDS = ["my recharge", "add yc", "myrecharge", "addyc"]
EARN_KEYWORDS = ["earn yc", "earnyc", "yc earn", "ycearn"]

def get_json_data():
    try:
        response = requests.get(JSON_URL, timeout=5)
        return response.json()
    except:
        return None

def is_allowed_link(link: str) -> bool:
    if not link:
        return False
    link_lower = link.lower()
    base_link = link_lower.split("?")[0]
    for ext in ALLOWED_EXTENSIONS:
        if base_link.endswith(ext):
            return True
    for site in ALLOWED_SITES:
        if site in link_lower:
            return True
    return False

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        if new_member.is_bot:
            continue
        try:
            member_status = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=new_member.id)
            if member_status.status in ['member', 'administrator', 'creator']:
                sent_msg = await update.message.reply_text(f"স্বাগতম [{new_member.first_name}](tg://user?id={new_member.id})! আমাদের গ্রুপে আপনাকে স্বাগতম। 🎉", parse_mode='Markdown')
                context.job_queue.run_once(lambda ctx: ctx.bot.delete_message(chat_id=update.message.chat_id, message_id=sent_msg.message_id), 300)
            else:
                keyboard = [
                    [InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
                    [InlineKeyboardButton("✅ আমি জয়েন করেছি", callback_data=f"check_join_{new_member.id}")]
                ]
                sent_msg = await update.message.reply_text(f"স্বাগতম [{new_member.first_name}](tg://user?id={new_member.id})! দয়া করে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
                context.job_queue.run_once(lambda ctx: ctx.bot.delete_message(chat_id=update.message.chat_id, message_id=sent_msg.message_id), 300)
        except Exception as e:
            print("Error:", e)

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    text_to_check = message.text or message.caption or ""
    text_lower = text_to_check.lower()
    chat_type = message.chat.type

    if chat_type in ['group', 'supergroup']:
        is_admin = False
        try:
            user_id = message.from_user.id
            chat_member = await context.bot.get_chat_member(chat_id=message.chat_id, user_id=user_id)
            if chat_member.status in ['administrator', 'creator']:
                is_admin = True
        except Exception:
            pass

        if not is_admin:
            should_delete = False
            
            if message.forward_origin:
                should_delete = True
                
            if any(spam_word in text_lower for spam_word in SPAM_KEYWORDS):
                should_delete = True

            if not should_delete:
                mentions = re.findall(MENTION_REGEX, text_to_check)
                for mention in mentions:
                    username_to_check = mention.replace("@", "")
                    if username_to_check.lower() == CHANNEL_USERNAME.replace("@", "").lower():
                        continue
                    try:
                        mentioned_member = await context.bot.get_chat_member(chat_id=message.chat_id, user_id=f"@{username_to_check}")
                        if mentioned_member.status in ['left', 'kicked', 'restricted']:
                            should_delete = True
                            break
                    except Exception:
                        should_delete = True
                        break

            if not should_delete:
                urls_to_check = []
                entities = message.entities or message.caption_entities or []
                for entity in entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        urls_to_check.append(entity.url)
                    elif entity.type == MessageEntityType.URL:
                        if message.text:
                            urls_to_check.append(message.text[entity.offset:entity.offset + entity.length])
                        elif message.caption:
                            urls_to_check.append(message.caption[entity.offset:entity.offset + entity.length])
                raw_links = re.findall(LINK_REGEX, text_to_check)
                urls_to_check.extend(raw_links)

                for link in urls_to_check:
                    if not is_allowed_link(link):
                        should_delete = True
                        break

            if should_delete:
                try:
                    await message.delete()
                except Exception:
                    pass
                return

    if any(k in text_lower for k in EARN_KEYWORDS):
        mini_app_link = "https://t.me/mytv_agent_bot/myapp"
        keyboard = [[InlineKeyboardButton("🚀 YC আর্নিং অ্যাপ ওপেন করুন", url=mini_app_link)]]
        await message.reply_text("💰 **YC আর্নিং সিস্টেম:**\n\nপ্রতিদিন টাস্ক কমপ্লিট করে YC আয় করুন। শুরু করতে নিচের বাটনে ক্লিক করুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if any(k in text_lower for k in RECHARGE_KEYWORDS):
        recharge_text = (
            "💎 *MY TV-তে YC রিচার্জ করার নিয়ম*\n\n"
            "১️⃣ MY TV অ্যাপে প্রবেশ করে Profile > Recharge পেজে যান।\n"
            "২️⃣ Amount দিয়ে Next করুন এবং মেথড নাম্বার কপি করে Send Money করুন।\n"
            "৩️⃣ TrxID কপি করুন এবং MY TV অ্যাপে TrxID ও পেমেন্ট করা নাম্বারের শেষ ৩ ডিজিট দিয়ে Submit করুন।\n"
            "ইনস্ট্যান্ট ব্যালেন্স যোগ হবে!"
        )
        await message.reply_text(recharge_text, parse_mode='Markdown')
        return

    if "mygo" in text_lower or "my go" in text_lower:
        data = get_json_data()
        if data:
            keyboard = [[InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"])] for btn in data.get("buttons", [])]
            sent_msg = await message.reply_text(data.get("menu_text", "মেনু:"), reply_markup=InlineKeyboardMarkup(keyboard))
            context.job_queue.run_once(lambda ctx: ctx.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=sent_msg.message_id, reply_markup=None), 300)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("check_join_"):
        target_id = int(data.split("_")[2])
        if query.from_user.id != target_id:
            await query.answer("এটি আপনার জন্য নয়!", show_alert=True)
            return
        try:
            status = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=target_id)
            if status.status in ['member', 'administrator', 'creator']:
                await query.answer("ধন্যবাদ! চ্যানেলে জয়েন করার জন্য।", show_alert=True)
                await query.message.delete()
            else:
                await query.answer("আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)
        except:
            await query.answer("চেক করা সম্ভব হয়নি।", show_alert=True)
        return

    # --- অ্যাডমিন অ্যাপ্রুভ করলে গ্রুপে মেসেজ যাওয়ার লজিক (ইউজারনেম ফিক্স) ---
    if data.startswith("apv_"):
        parts = data.split("_")
        if len(parts) >= 4:
            user_id = parts[1]
            amount = parts[2]
            wallet_id = "_".join(parts[3:]) 
            
            # অ্যাডমিনের মেসেজ থেকে আসল ইউজারনেম বের করা হচ্ছে
            real_username = "মেম্বার"
            if query.message and query.message.text:
                match = re.search(r"👤 ইউজার:\s*@?([^\s\(]+)", query.message.text)
                if match:
                    real_username = match.group(1)
            
            await query.answer("উইথড্র সফলভাবে অ্যাপ্রুভ করা হয়েছে!")
            await query.edit_message_text(f"✅ উইথড্র অ্যাপ্রুভড\n👤 User: @{real_username}\n💳 Wallet: `{wallet_id}`\n💰 Amount: {amount} YC", parse_mode='Markdown')
            
            # গ্রুপে মেসেজ পাঠানোর সময় আসল নাম ব্যবহার করা হচ্ছে
            success_msg = (
                f"🎉 **উইথড্র সাকসেসফুল!**\n\n"
                f"👤 ইউজার: [{real_username}](tg://user?id={user_id})\n"
                f"💳 ওয়ালেট আইডি: `{wallet_id}`\n"
                f"💰 পরিমাণ: **{amount} YC**\n\n"
                f"✅ আপনার ওয়ালেটে ব্যালেন্স সফলভাবে অ্যাড করা হয়েছে!"
            )
            try:
                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=success_msg, parse_mode='Markdown')
            except Exception as e:
                print(f"Error sending group message: {e}")
        return

    await query.answer()
    data_key = query.data
    json_data = get_json_data()
    if json_data and "answers" in json_data:
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        await query.message.reply_text(json_data["answers"].get(data_key, "তথ্য নেই।"))

@web_app.route('/api/withdraw', methods=['POST'])
def api_withdraw():
    req_data = request.json
    wallet_id = req_data.get('wallet_id')
    amount = req_data.get('amount')
    telegram_user = req_data.get('username', 'Unknown')
    user_id = req_data.get('user_id', '0')

    if ADMIN_CHAT_ID:
        callback_data = f"apv_{user_id}_{amount}_{wallet_id}"
        if len(callback_data) > 64:
            callback_data = callback_data[:64]
            
        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ Approve", "callback_data": callback_data}]
            ]
        }
        
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                "chat_id": ADMIN_CHAT_ID,
                "text": f"🔔 **নতুন উইথড্র রিকোয়েস্ট!**\n\n👤 ইউজার: @{telegram_user} (ID: `{user_id}`)\n💳 ওয়ালেট আইডি: `{wallet_id}`\n💵 পরিমাণ: {amount} YC",
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            }, timeout=5)
        except Exception as e:
            print("Failed to send admin message:", e)

    return jsonify({"status": "success", "message": "Withdraw request sent!"})

def main():
    if not TOKEN:
        return
    threading.Thread(target=run_web, daemon=True).start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.NEW_CHAT_MEMBERS, check_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("বট এবং ওয়েব অ্যাপ সফলভাবে চালু হয়েছে...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
