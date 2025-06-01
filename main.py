import os
import random
from datetime import datetime, timedelta
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

# عکس پایانی پیام‌ها
FINAL_IMAGE_URL = "https://uploadkon.ir/uploads/96a601_25photo18968523702.jpg"

# ==== توابع کمکی ====

def send_photo_with_caption(chat_id, text, reply_to_message_id=None, parse_mode='Markdown'):
    try:
        msg = bot.send_photo(chat_id, photo=FINAL_IMAGE_URL, caption=text, reply_to_message_id=reply_to_message_id, parse_mode=parse_mode)
        return msg
    except Exception as e:
        print("[ERROR] send photo with caption:", e)
        # اگر عکس ارسال نشد، فقط متن را بفرست
        return bot.send_message(chat_id, text, reply_to_message_id=reply_to_message_id, parse_mode=parse_mode)

def send_reply_photo_with_caption(message, text, parse_mode='Markdown'):
    return send_photo_with_caption(message.chat.id, text, reply_to_message_id=message.message_id, parse_mode=parse_mode)

def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return user_id in custom_admins or any(admin.user.id == user_id for admin in admins)
    except Exception as e:
        print("[ERROR] is_admin:", e)
        return False

def mention_user(user):
    return f"[{user.first_name}](tg://user?id={user.id})"

# ==== Webhook ====
@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "ربات فعال است ✅"

# ==== پیام خصوصی ====
@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    if message.chat.type == 'private':
        send_reply_photo_with_caption(message, "Welcome To Moscow 🌙\nDeveloper : @rewhi 👑")

# ==== خوش‌آمدگویی ====
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message: Message):
    for member in message.new_chat_members:
        try:
            photos = bot.get_user_profile_photos(member.id, limit=1)
            if photos.total_count > 0:
                bot.send_photo(
                    message.chat.id,
                    photos.photos[0][0].file_id,
                    caption=f"🤤 ممبر جدید {mention_user(member)}!",
                    parse_mode='Markdown'
                )
            else:
                send_photo_with_caption(message.chat.id, f"🤤 ممبر جدید {mention_user(member)}!", parse_mode='Markdown')
        except Exception as e:
            print("[ERROR] welcome:", e)

# ==== پیام‌های گروه ====
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.text)
def handle_group_message(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    lower = text.lower()

    stats = group_stats.setdefault(chat_id, {'messages': 0, 'users': {}})
    stats['messages'] += 1
    stats['users'][user_id] = stats['users'].get(user_id, 0) + 1

    group_users.setdefault(chat_id, set()).add(user_id)

    # فیلتر کلمات ممنوع
    if any(w in lower for w in FILTERED_WORDS):
        try:
            bot.delete_message(chat_id, message.message_id)
            send_photo_with_caption(chat_id, f"⚠️ {mention_user(message.from_user)} بی‌ادبی نکن!", parse_mode='Markdown')
        except Exception as e:
            print("[ERROR] filter:", e)
        return

    # فقط ادمین‌ها مجاز به دستورات زیر هستند
    if not is_admin(chat_id, user_id):
        return

    if lower.startswith("ارسال"):
        msg = text[5:].strip()
        if not msg:
            send_reply_photo_with_caption(message, "❗ لطفاً متنی بنویس.")
            return
        success, fail = 0, 0
        for uid in group_users[chat_id]:
            try:
                bot.send_message(uid, f"""👑 پیام از {message.chat.title}:\n\n{msg}""")
                success += 1
            except Exception:
                fail += 1
        send_reply_photo_with_caption(message, f"✅ ارسال: {success}\n❌ شکست: {fail}")

    elif lower.startswith("سیک") and message.reply_to_message:
        try:
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            send_reply_photo_with_caption(message, f"✅ {mention_user(message.reply_to_message.from_user)} بن شد.")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower.startswith("حذف سیک") and message.reply_to_message:
        try:
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            send_reply_photo_with_caption(message, "✅ آزاد شد.")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower.startswith("خفه") and message.reply_to_message and lower == "خفه":
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=False))
            send_reply_photo_with_caption(message, "🔇 خفه شد.")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower.startswith("حذف خفه") and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=True))
            send_reply_photo_with_caption(message, "🔊 آزاد شد.")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower.startswith("خفه موقت") and message.reply_to_message:
        try:
            parts = lower.split()
            if len(parts) < 3:
                send_reply_photo_with_caption(message, "❗ استفاده صحیح: خفه موقت [ثانیه] (ریپلی روی پیام)")
                return
            duration = int(parts[2])
            until = datetime.utcnow() + timedelta(seconds=duration)
            bot.restrict_chat_member(
                chat_id, 
                message.reply_to_message.from_user.id, 
                until_date=until,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            send_reply_photo_with_caption(message, f"⏱️ خفه موقت شد ({duration} ثانیه)")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower.startswith("پاکسازی"):
        try:
            parts = lower.split()
            if len(parts) < 2 or not parts[1].isdigit():
                send_reply_photo_with_caption(message, "❗ استفاده صحیح: پاکسازی [تعداد]")
                return
            count = int(parts[1])
            for i in range(count):
                try:
                    bot.delete_message(chat_id, message.message_id - i)
                except:
                    pass
            send_reply_photo_with_caption(message, f"🗑️ {count} پیام حذف شد.")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower == "قفل":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False))
            send_reply_photo_with_caption(message, "🔒 گروه قفل شد.")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower == "باز کردن":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True))
            send_reply_photo_with_caption(message, "🔓 گروه باز شد.")
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower.startswith("افزودن ادمین"):
        parts = lower.split()
        if len(parts) >= 3 and parts[-1] == ADMIN_PASSWORD:
            custom_admins.add(user_id)
            send_reply_photo_with_caption(message, "👮 ادمین شدی.")
        else:
            send_reply_photo_with_caption(message, "❌ رمز نادرست است.")

    elif lower == "ادمین ها":
        try:
            admins = bot.get_chat_administrators(chat_id)
            reply = "\n".join([f"👮 {mention_user(a.user)}" for a in admins])
            send_reply_photo_with_caption(message, reply)
        except Exception as e:
            send_reply_photo_with_caption(message, f"❌ خطا: {e}")

    elif lower == "جوک":
        send_reply_photo_with_caption(message, random.choice(JOKES))

    elif lower == "امار":
        s = group_stats.get(chat_id)
        if not s:
            send_reply_photo_with_caption(message, "📊 آماری موجود نیست.")
            return
        reply = "📊 *آمار گروه:*\n\n"
        reply += f"📝 تعداد کل پیام‌ها: *{s['messages']}*\n\n"
        reply += "👥 *برترین ارسال‌کنندگان پیام:* \n"
        for uid, count in sorted(s['users'].items(), key=lambda x: x[1], reverse=True)[:5]:
            try:
                user = bot.get_chat_member(chat_id, uid).user
                user_mention = f"[{user.first_name}](tg://user?id={user.id})"
            except Exception:
                user_mention = f"`{uid}`"
            reply += f"➤ {user_mention} — {count} پیام\n"

        send_reply_photo_with_caption(message, reply)

    elif lower == "راهنما":
        send_reply_photo_with_caption(message, """
✨ راهنمای کاربر :

🚫 سیک - بن کاربر (ریپلی روی پیام)
♻️ حذف سیک - آزاد کردن کاربر (ریپلی روی پیام)
🔕 خفه - سکوت دائمی کاربر (ریپلی روی پیام)
🔕 خفه موقت [ثانیه] - سکوت موقت کاربر (ریپلی روی پیام)
🔊 حذف خفه - لغو سکوت (ریپلی روی پیام)
🗑 پاکسازی [تعداد] - حذف پیام‌ها
🔐 قفل - قفل گروه
🔓 باز کردن - بازکردن گروه
🧸 افزودن ادمین [رمز] - افزودن ادمین شخصی
🗂 ادمین ها - لیست ادمین‌ها
😂 جوک - گفتن جوک تصادفی
📊 امار - نمایش آمار گروه
🔰 راهنما - نمایش این پیام

⚜ اختصاصی تیم **Moscow Nights**
        """)

# ==== اجرای ربات ====
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
