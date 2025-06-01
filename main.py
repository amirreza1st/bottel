import os
import random
from datetime import datetime, timedelta
import requests
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import Message

# ==== تنظیمات اولیه ====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
    raise Exception("توکن یا Webhook URL مشخص نشده!")

bot = TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# ==== داده‌ها و پیکربندی ====
ADMIN_PASSWORD = "1111"
custom_admins = set()
FILTERED_WORDS = [
    "کص", "کوص", "ننت", "مادرت", "مامانت", "ننه", "جنده",
    "کونده", "کصده", "خارت", "خواهرتو", "کوس", "ابجیتو",
    "کونتو", "لینک"
]

JOKES = [
    "🤣 چرا کامپیوتر هیچ‌وقت گرسنه نیست؟ چون همیشه RAM داره!",
    "😆 چرا برنامه‌نویس‌ها از طبیعت خوششون نمیاد؟ چون باگ زیاده!",
    "‏به یکی گفتم: چقد خوشگلی!! گفت: چشات قشنگ میبینه. دو تا عکس که رفتم جلوتر دیدم راست میگفته بنده‌خدا",
    "حیف نون ﺑﺎﺑﺎﺵ ﻣﯿﻤﯿﺮﻩ، ﺳﻮﻣﺶ ﺧﯿﻠﯽ ﺷﻠﻮﻍ ﻣﯿﺸﻪ، به ﺩﺍﺩﺍﺷﺶ ﻣﯿﮕﻪ ﺍﮔﻪ ﻫﻔﺘﻢ ﻫﻢ ﺍﯾﻨﻘﺪ ﺷﻠﻮﻍ ﺷﺪ ﺑﻼﻝ ﺑﯿﺎﺭﯾﻢ ﺑﻔﺮﻭﺷﯿﻢ",
    "حیوون خوونگی فقط مورچه!! سر و صدا نمیکنه، جیش نمی‌کنه، رسیدگی نمی‌خواد، آروم خونه رو جارو می‌کنه، گشنه هم بشه یه چیزی از رو فرش پیدا می‌کنه می‌خوره"
]

group_users = {}  # {chat_id: set(user_id)}
group_stats = {}  # {chat_id: {'messages': int, 'users': {user_id: count}}}

# ==== Webhook ====
@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def receive_update():
    update = types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "ربات فعال است ✅"

# ==== توابع کمکی ====
def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return user_id in custom_admins or any(admin.user.id == user_id for admin in admins)
    except:
        return False

def mention_user(user):
    return f"[{user.first_name}](tg://user?id={user.id})"

# ==== پیام خصوصی ==== 
@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Welcome To Moscow 🌙\nDeveloper : @rewhi 👑")

# ==== خوش‌آمدگویی ====
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message: Message):
    for member in message.new_chat_members:
        try:
            photos = bot.get_user_profile_photos(member.id, limit=1)
            if photos.total_count > 0:
                bot.send_photo(message.chat.id, photos.photos[0][0].file_id, caption=f"🤤 ممبر جدید {mention_user(member)}!", parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, f"🤤 ممبر جدید {mention_user(member)}!", parse_mode='Markdown')
        except Exception as e:
            print("[ERROR] welcome:", e)

# ==== پیام‌های گروه ====
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.text)
def handle_group_message(message: Message):
    user_id, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()

    # آمار
    stats = group_stats.setdefault(chat_id, {'messages': 0, 'users': {}})
    stats['messages'] += 1
    stats['users'][user_id] = stats['users'].get(user_id, 0) + 1

    # ثبت کاربر
    group_users.setdefault(chat_id, set()).add(user_id)

    # فیلتر کلمات ممنوع
    if any(w in text.lower() for w in FILTERED_WORDS):
        try:
            bot.delete_message(chat_id, message.message_id)
            bot.send_message(chat_id, f"⚠️ {mention_user(message.from_user)} بی‌ادبی نکن!", parse_mode='Markdown')
        except:
            pass
        return

    # دستورها
    if not is_admin(chat_id, user_id):
        return

    lower = text.lower()

    if lower.startswith("ارسال"):
        msg = text[5:].strip()
        if not msg:
            bot.reply_to(message, "❗ لطفاً متنی بنویس.")
            return
        success, fail = 0, 0
        for uid in group_users[chat_id]:
            try:
                bot.send_message(uid, f"📩 پیام از {message.chat.title"}:

{msg}", parse_mode='Markdown')
                success += 1
            except:
                fail += 1
        bot.reply_to(message, f"✅ ارسال: {success}\n❌ شکست: {fail}")

    elif lower.startswith("سیک") and message.reply_to_message:
        try:
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            bot.reply_to(message, f"✅ {mention_user(message.reply_to_message.from_user)} بن شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower.startswith("حذف سیک") and message.reply_to_message:
        try:
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            bot.reply_to(message, f"✅ آزاد شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower.startswith("خفه") and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=False))
            bot.reply_to(message, f"🔇 خفه شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower.startswith("حذف خفه") and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=True))
            bot.reply_to(message, f"🔊 آزاد شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower.startswith("خفه موقت") and message.reply_to_message:
        try:
            duration = int(lower.split()[1])
            until = datetime.utcnow() + timedelta(seconds=duration)
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, until_date=until, permissions=types.ChatPermissions(can_send_messages=False))
            bot.reply_to(message, f"⏱️ خفه موقت شد ({duration} ثانیه)")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower.startswith("پاکسازی") and message.reply_to_message:
        try:
            count = int(lower.split()[1])
            for i in range(count):
                bot.delete_message(chat_id, message.reply_to_message.message_id + i)
            bot.reply_to(message, f"🗑️ {count} پیام حذف شد.")
        except:
            bot.reply_to(message, "❗ استفاده صحیح: پاکسازی [تعداد]")

    elif lower == "قفل":
        bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False))
        bot.reply_to(message, "🔒 گروه قفل شد.")

    elif lower == "باز کردن":
        bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True))
        bot.reply_to(message, "🔓 گروه باز شد.")

    elif lower.startswith("افزودن ادمین"):
        if lower.split()[-1] == ADMIN_PASSWORD:
            custom_admins.add(user_id)
            bot.reply_to(message, "👮 ادمین شدی.")
        else:
            bot.reply_to(message, "❌ رمز نادرست است.")

    elif lower == "ادمین ها":
        try:
            admins = bot.get_chat_administrators(chat_id)
            reply = "\n".join([f"👮 {mention_user(a.user)}" for a in admins])
            bot.reply_to(message, reply, parse_mode='Markdown')
        except:
            pass

    elif lower == "جوک":
        bot.reply_to(message, random.choice(JOKES))

    elif lower == "آمار":
        s = group_stats.get(chat_id)
        if not s:
            bot.reply_to(message, "📊 آماری موجود نیست.")
            return
        reply = f"📊 آمار گروه:\n🔢 پیام‌ها: {s['messages']}\n"
        for uid, count in sorted(s['users'].items(), key=lambda x: x[1], reverse=True)[:5]:
            reply += f"- [{uid}](tg://user?id={uid}): {count} پیام\n"
        bot.reply_to(message, reply, parse_mode='Markdown')

    elif lower == "راهنما":
        bot.reply_to(message, """
✨ راهنمای کاربر :

🚫 سیک - بن کاربر
♻️ حذف سیک - آزاد کردن کاربر
🔕 خفه - سکوت دائمی کاربر
🔕 خفه موقت - سکوت موقت کاربر
🔊 حذف خفه - لغو سکوت
🗑 پاکسازی - حذف پیام ها
🔐 قفل - قفل گروه
🔓 باز کردن - بازکردن گروه
🧸 افزودن ادمین - ادمین جدید
🗂 ادمین ها - لیست ادمین ها
😂 جوک - جوک گفتن
📊 امار - آمار گروه
🔰 راهنما - راهنمای دستورات

⚜ اختصاصی تیم **{Moscow Nights}**
        """, parse_mode='Markdown')

# ==== اجرای ربات ====
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
