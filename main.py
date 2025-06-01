import os
import random
from datetime import datetime, timedelta
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import Message

# ==== تنظیمات اولیه ====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if TELEGRAM_BOT_TOKEN is None or WEBHOOK_URL is None:
    raise Exception("توکن یا Webhook URL مشخص نشده!")

bot = TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

ADMIN_PASSWORD = "1494"
custom_admins = set()
FILTERED_WORDS = ["بد", "زشت"]
JOKES = [
    "🤣 چرا کامپیوتر هیچ‌وقت گرسنه نیست؟ چون همیشه RAM داره!",
    "😆 چرا برنامه‌نویس‌ها از طبیعت خوششون نمیاد؟ چون باگ زیاده!"
]

# ==== Webhook ====
@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def root():
    return "ربات فعال است ✅"

# ==== توابع کمکی ====

def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins) or user_id in custom_admins
    except Exception:
        return False

def mention_user(user):
    # قالب منشن با MarkdownV2
    return f"[{user.first_name}](tg://user?id={user.id})"

# ==== هندلر دستور /start (فقط چت خصوصی) ====
@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Welcome To Moscow 🌙\nDeveloper : @rewhi 👑")

# ==== خوش‌آمدگویی با عکس پروفایل ====
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message: Message):
    for new_member in message.new_chat_members:
        try:
            # گرفتن عکس پروفایل (حداقل سایز 1)
            photos = bot.get_user_profile_photos(new_member.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][0].file_id
                bot.send_photo(
                    message.chat.id,
                    photo=file_id,
                    caption=f"🎉 خوش آمدی {mention_user(new_member)}!",
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(message.chat.id, f"🎉 خوش آمدی {mention_user(new_member)}!", parse_mode='Markdown')
        except Exception as e:
            print(f"[ERROR] welcome_new_members: {e}")
            bot.send_message(message.chat.id, f"🎉 خوش آمدی {mention_user(new_member)}!", parse_mode='Markdown')

# ==== هندلر پیام‌های گروه: فیلتر کلمات و دستورها ====
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.text)
def group_message_handler(message: Message):
    print(f"[DEBUG] پیام گروهی از {message.from_user.id}: {message.text}")

    # فیلتر کلمات ممنوع
    for word in FILTERED_WORDS:
        if word in message.text.lower():
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"⚠️ {mention_user(message.from_user)} لطفاً از الفاظ مناسب استفاده کن.", parse_mode='Markdown')
            except Exception:
                pass
            return

    # فقط ادمین‌ها اجازه اجرای دستور را دارند
    if not is_admin(message.chat.id, message.from_user.id):
        return

    text = message.text.strip().lower()

    if text.startswith("ban") and message.reply_to_message:
        try:
            bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, f"✅ {mention_user(message.reply_to_message.from_user)} کاربر بن شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif text.startswith("unban") and message.reply_to_message:
        try:
            bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, f"✅ {mention_user(message.reply_to_message.from_user)} آزاد شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif text.startswith("mute") and message.reply_to_message:
        try:
            bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            bot.reply_to(message, f"🔇 {mention_user(message.reply_to_message.from_user)} کاربر ساکت شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif text.startswith("unmute") and message.reply_to_message:
        try:
            bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                permissions=types.ChatPermissions(can_send_messages=True)
            )
            bot.reply_to(message, f"🔊 {mention_user(message.reply_to_message.from_user)} لغو سکوت شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif text.startswith("tempmute") and message.reply_to_message:
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            try:
                duration = int(parts[1])
                until = datetime.utcnow() + timedelta(seconds=duration)
                bot.restrict_chat_member(
                    message.chat.id,
                    message.reply_to_message.from_user.id,
                    until_date=until,
                    permissions=types.ChatPermissions(can_send_messages=False)
                )
                bot.reply_to(message, f"⏱️ {mention_user(message.reply_to_message.from_user)} به مدت {duration} ثانیه ساکت شد.", parse_mode='Markdown')
            except Exception as e:
                bot.reply_to(message, f"❌ خطا: {e}")
        else:
            bot.reply_to(message, "❗ استفاده صحیح: tempmute [ثانیه] (با ریپلای)")

    elif text.startswith("del") and message.reply_to_message:
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            count = int(parts[1])
            deleted = 0
            for i in range(count):
                try:
                    bot.delete_message(message.chat.id, message.reply_to_message.message_id + i)
                    deleted += 1
                except Exception:
                    pass
            bot.reply_to(message, f"🗑️ {deleted} پیام حذف شد.")
        else:
            bot.reply_to(message, "❗ استفاده صحیح: del [تعداد] (با ریپلای)")

    elif text == "lock":
        try:
            bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=False))
            bot.reply_to(message, "🔒 گروه قفل شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif text == "unlock":
        try:
            bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=True))
            bot.reply_to(message, "🔓 گروه باز شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif text.startswith("addadmin"):
        parts = text.split()
        if len(parts) == 2 and parts[1] == ADMIN_PASSWORD:
            custom_admins.add(message.from_user.id)
            bot.reply_to(message, "✅ شما به عنوان ادمین ثبت شدید.")
        else:
            bot.reply_to(message, "❌ رمز نادرست است.")

    elif text == "admins":
        try:
            admins = bot.get_chat_administrators(message.chat.id)
            names = [f"👮 {mention_user(admin.user)}" for admin in admins]
            bot.reply_to(message, "لیست مدیران:\n" + "\n".join(names), parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif text == "joke":
        bot.reply_to(message, random.choice(JOKES))

    elif text == "help":
        bot.reply_to(message, """
📖 راهنمای ربات:

🔨 ban (با ریپلای) - بن کاربر  
🔓 unban - آزاد کردن  
🔇 mute - سکوت دائمی  
⏱️ tempmute [ثانیه] - سکوت موقت  
🔊 unmute - لغو سکوت  
🗑️ del [تعداد] - حذف پیام‌ها  
🔒 lock - قفل گروه  
🔓 unlock - باز کردن  
🎭 addadmin [رمز] - افزودن ادمین  
📋 admins - لیست ادمین‌ها  
🤣 joke - جوک  
📌 help - نمایش راهنما
""")

# ==== اجرای برنامه ====
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
