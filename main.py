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

# ==== توابع کمکی ====
def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return user_id in custom_admins or any(admin.user.id == user_id for admin in admins)
    except Exception as e:
        print("[ERROR] is_admin:", e)
        return False

def mention_user(user):
    # اسم کاربر را با لینک قابل کلیک برمی‌گرداند
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
                bot.send_photo(
                    message.chat.id,
                    photos.photos[0][0].file_id,
                    caption=f"🤤 ممبر جدید {mention_user(member)}!",
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    f"🤤 ممبر جدید {mention_user(member)}!",
                    parse_mode='Markdown'
                )
        except Exception as e:
            print("[ERROR] welcome:", e)

# ==== پیام‌های گروه ====
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.text)
def handle_group_message(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    lower = text.lower()

    # آمار پیام‌ها و کاربران
    stats = group_stats.setdefault(chat_id, {'messages': 0, 'users': {}})
    stats['messages'] += 1
    stats['users'][user_id] = stats['users'].get(user_id, 0) + 1

    # ثبت کاربر در گروه
    group_users.setdefault(chat_id, set()).add(user_id)

    # فیلتر کلمات ممنوع
    if any(w in lower for w in FILTERED_WORDS):
        try:
            bot.delete_message(chat_id, message.message_id)
            bot.send_message(chat_id, f"⚠️ {mention_user(message.from_user)} بی‌ادبی نکن!", parse_mode='Markdown')
        except Exception as e:
            print("[ERROR] filter:", e)
        return

    # فقط ادمین‌ها مجاز به دستورات زیر هستند
    if not is_admin(chat_id, user_id):
        return

    # دستورات ادمین‌ها

    # ارسال پیام خصوصی به تمام کاربران گروه
    if lower.startswith("ارسال"):
        msg = text[5:].strip()
        if not msg:
            bot.reply_to(message, "❗ لطفاً متنی بنویس.")
            return
        success, fail = 0, 0
        for uid in group_users[chat_id]:
            try:
                bot.send_message(uid, f"""👑 پیام از {message.chat.title}:

{msg}""")
                success += 1
            except Exception:
                fail += 1
        bot.reply_to(message, f"✅ ارسال: {success}\n❌ شکست: {fail}")

    # بن کردن کاربر (ریپلی روی پیام کاربر)
    elif lower.startswith("سیک") and message.reply_to_message:
        try:
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            bot.reply_to(message, f"✅ {mention_user(message.reply_to_message.from_user)} بن شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # آزاد کردن کاربر
    elif lower.startswith("حذف سیک") and message.reply_to_message:
        try:
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "✅ آزاد شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # خفه کردن (سکوت دائمی)
    elif lower.startswith("خفه") and message.reply_to_message and lower == "خفه":
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=False))
            bot.reply_to(message, "🔇 خفه شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # حذف خفه (لغو سکوت)
    elif lower.startswith("حذف خفه") and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=True))
            bot.reply_to(message, "🔊 آزاد شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # خفه موقت با مدت زمان (ثانیه)
    elif lower.startswith("خفه موقت") and message.reply_to_message:
        try:
            parts = lower.split()
            if len(parts) < 3:
                bot.reply_to(message, "❗ استفاده صحیح: خفه موقت [ثانیه] (ریپلی روی پیام)")
                return
            duration = int(parts[2])  # فرض می‌کنیم دستور: "خفه موقت reply 60"
            until = datetime.utcnow() + timedelta(seconds=duration)
            bot.restrict_chat_member(
                chat_id, 
                message.reply_to_message.from_user.id, 
                until_date=until,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            bot.reply_to(message, f"⏱️ خفه موقت شد ({duration} ثانیه)")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # پاکسازی پیام‌ها (با تعداد)
    elif lower.startswith("پاکسازی"):
        try:
            parts = lower.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "❗ استفاده صحیح: پاکسازی [تعداد]")
                return
            count = int(parts[1])
            for i in range(count):
                try:
                    bot.delete_message(chat_id, message.message_id - i)
                except:
                    pass
            bot.reply_to(message, f"🗑️ {count} پیام حذف شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # قفل گروه (غیر فعال کردن ارسال پیام برای همه)
    elif lower == "قفل":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False))
            bot.reply_to(message, "🔒 گروه قفل شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # بازکردن گروه (فعال کردن ارسال پیام)
    elif lower == "باز کردن":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True))
            bot.reply_to(message, "🔓 گروه باز شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # افزودن ادمین شخصی با رمز عبور
    elif lower.startswith("افزودن ادمین"):
        parts = lower.split()
        if len(parts) >= 3 and parts[-1] == ADMIN_PASSWORD:
            custom_admins.add(user_id)
            bot.reply_to(message, "👮 ادمین شدی.")
        else:
            bot.reply_to(message, "❌ رمز نادرست است.")

    # لیست ادمین‌ها
    elif lower == "ادمین ها":
        try:
            admins = bot.get_chat_administrators(chat_id)
            reply = "\n".join([f"👮 {mention_user(a.user)}" for a in admins])
            bot.reply_to(message, reply, parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    # جوک گفتن
    elif lower == "جوک":
        bot.reply_to(message, random.choice(JOKES))

# نمایش آمار گروه
elif lower == "امار":
    s = group_stats.get(chat_id)
    if not s:
        bot.reply_to(message, "📊 آماری موجود نیست.")
        return
    reply = "📊 *آمار گروه:*\n\n"
    reply += f"📝 تعداد کل پیام‌ها: *{s['messages']}*\n\n"
    reply += "👥 *برترین ارسال‌کنندگان پیام:* \n"
    for uid, count in sorted(s['users'].items(), key=lambda x: x[1], reverse=True)[:5]:
        try:
            user = bot.get_chat_member(chat_id, uid).user
            user_mention = f"[{user.first_name}](tg://user?id={user.id})"
        except Exception:
            # اگر مشکلی بود فقط آی‌دی را نشان بده
            user_mention = f"`{uid}`"
        reply += f"➤ {user_mention} — {count} پیام\n"

    bot.reply_to(message, reply, parse_mode='Markdown')

    # ارسال عکس در پایان پیام آمار (آدرس عکس را تغییر دهید به URL دلخواه)
    image_url = "https://uploadkon.ir/uploads/96a601_25photo18968523702.jpg"
    try:
        bot.send_photo(chat_id, image_url)
    except Exception as e:
        print("[ERROR] send photo in stats:", e)

    # راهنما
    elif lower == "راهنما":
        bot.reply_to(message, """
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
        """, parse_mode='Markdown')

# ==== اجرای ربات ====
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
