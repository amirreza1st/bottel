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

ADMIN_PASSWORD = "1111"
custom_admins = set()
FILTERED_WORDS = ["کص", "کوص", "ننت", "مادرت", "مامانت", "ننه", "جنده", "کونده", "کصده", "خارت", "خواهرتو", "کوس", "ابجیتو", "کونتو", "لینک"]
JOKES = [
    "🤣 چرا کامپیوتر هیچ‌وقت گرسنه نیست؟ چون همیشه RAM داره!",
    "😆 چرا برنامه‌نویس‌ها از طبیعت خوششون نمیاد؟ چون باگ زیاده!",
    """‏به یکی گفتم: چقد خوشگلی!!

گفت: چشات قشنگ میبینه.

دو تا عکس که رفتم جلوتر دیدم راست میگفته بنده‌خدا""",
    """حیف نون ﺑﺎﺑﺎﺵ ﻣﯿﻤﯿﺮﻩ

ﺳﻮﻣﺶ ﺧﯿﻠﯽ ﺷﻠﻮﻍ ﻣﯿﺸﻪ، 

😆 ﺑﻪ ﺩﺍﺩﺍﺷﺶ ﻣﯿﮕﻪ ﺍﮔﻪ ﻫﻔﺘﻢ ﻫﻢ ﺍﯾﻨﻘﺪ ﺷﻠﻮﻍ ﺷﺪ ﺑﻼﻝ ﺑﯿﺎﺭﯾﻢ ﺑﻔﺮﻭﺷﯿﻢ""",
    """حیوون خوونگی فقط مورچه!!

سر و صدا نمیکنه ،جیش نمی کنه، رسیدگی نمیخواد

آروم خونه رو جارو میکنه

گشنه هم بشه یه چیزی از رو فرش پیدا میکنه می خوره """
]

# دیکشنری ذخیره اعضای هر گروه (کلید: chat_id، مقدار: set از user_id ها)
group_users = {}

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
            photos = bot.get_user_profile_photos(new_member.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][0].file_id
                bot.send_photo(
                    message.chat.id,
                    photo=file_id,
                    caption=f"🤤 ممبر جدید {mention_user(new_member)}!",
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(message.chat.id, f"🤤 ممبر جدید {mention_user(new_member)}!", parse_mode='Markdown')
        except Exception as e:
            print(f"[ERROR] welcome_new_members: {e}")
            bot.send_message(message.chat.id, f"🤤 ممبر جدید {mention_user(new_member)}!", parse_mode='Markdown')

# ==== هندلر پیام‌های گروه: فیلتر کلمات، دستورها، و ارسال پیام خصوصی ====
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.text)
def group_message_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()

    print(f"[DEBUG] پیام گروهی از {user_id}: {text}")

    # ثبت عضو در دیکشنری
    users = group_users.setdefault(chat_id, set())
    users.add(user_id)

    # فیلتر کلمات ممنوع
    for word in FILTERED_WORDS:
        if word in text.lower():
            try:
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"⚠️ {mention_user(message.from_user)} بی ادبی نکن گوساله.", parse_mode='Markdown')
            except Exception:
                pass
            return

    # فقط ادمین‌ها اجازه اجرای دستور را دارند (بجز مواردی که نیاز به ادمین نیست)
    # دستور ارسال پیام خصوصی به اعضا
    if text.lower().startswith("ارسال"):
        if not is_admin(chat_id, user_id):
            return
        text_to_send = text[5:].strip()
        if not text_to_send:
            bot.reply_to(message, "❗ لطفاً متنی برای ارسال خصوصی وارد کنید.")
            return
        sent_count = 0
        failed_count = 0
        for uid in users:
            try:
                user_mention = f"[کاربر](tg://user?id={uid})"
                bot.send_message(uid, f"پیام از گروه {message.chat.title}:\n\n{text_to_send}\n\n{user_mention}", parse_mode='Markdown')
                sent_count += 1
            except Exception:
                failed_count += 1
        bot.reply_to(message, f"✅ پیام به {sent_count} نفر ارسال شد.\n❌ ارسال به {failed_count} نفر موفق نبود.")
        return

    # دستورهای ادمین که ریپلای لازم دارند
    if not is_admin(chat_id, user_id):
        return

    lower_text = text.lower()

    if lower_text.startswith("سیک") and message.reply_to_message:
        try:
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            bot.reply_to(message, f"✅ {mention_user(message.reply_to_message.from_user)} سیک کاربر رو زدم.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower_text.startswith("حذف سیک") and message.reply_to_message:
        try:
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            bot.reply_to(message, f"✅ {mention_user(message.reply_to_message.from_user)} آزاد شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower_text.startswith("خفه") and message.reply_to_message:
        try:
            bot.restrict_chat_member(
                chat_id,
                message.reply_to_message.from_user.id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            bot.reply_to(message, f"🔇 {mention_user(message.reply_to_message.from_user)} کاربر خفه شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower_text.startswith("حذف خفه") and message.reply_to_message:
        try:
            bot.restrict_chat_member(
                chat_id,
                message.reply_to_message.from_user.id,
                permissions=types.ChatPermissions(can_send_messages=True)
            )
            bot.reply_to(message, f"🔊 {mention_user(message.reply_to_message.from_user)} ازاد شد.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower_text.startswith("خفه موقت") and message.reply_to_message:
        parts = lower_text.split()
        if len(parts) == 2 and parts[1].isdigit():
            try:
                duration = int(parts[1])
                until = datetime.utcnow() + timedelta(seconds=duration)
                bot.restrict_chat_member(
                    chat_id,
                    message.reply_to_message.from_user.id,
                    until_date=until,
                    permissions=types.ChatPermissions(can_send_messages=False)
                )
                bot.reply_to(message, f"⏱️ {mention_user(message.reply_to_message.from_user)} به مدت {duration} ثانیه خفه شد.", parse_mode='Markdown')
            except Exception as e:
                bot.reply_to(message, f"❌ خطا: {e}")
        else:
            bot.reply_to(message, "❗ استفاده صحیح: tempmute [ثانیه] (با ریپلای)")

    elif lower_text.startswith("پاکسازی") and message.reply_to_message:
        parts = lower_text.split()
        if len(parts) == 2 and parts[1].isdigit():
            count = int(parts[1])
            deleted = 0
            for i in range(count):
                try:
                    bot.delete_message(chat_id, message.reply_to_message.message_id + i)
                    deleted += 1
                except Exception:
                    pass
            bot.reply_to(message, f"🗑️ {deleted} پیام حذف شد.")
        else:
            bot.reply_to(message, "❗ استفاده صحیح: del [تعداد] (با ریپلای)")

    elif lower_text == "قفل":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False))
            bot.reply_to(message, "🔒 گروه قفل شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower_text == "باز کردن":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True))
            bot.reply_to(message, "🔓 گروه باز شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower_text.startswith("افزودن ادمین"):
        parts = lower_text.split()
        if len(parts) == 2 and parts[1] == ADMIN_PASSWORD:
            custom_admins.add(user_id)
            bot.reply_to(message, "🥰 شما به عنوان ادمین ثبت شدید.")
        else:
            bot.reply_to(message, "❌ رمز نادرست است.")

    elif lower_text == "ادمین ها":
        try:
            admins = bot.get_chat_administrators(chat_id)
            names = [f"👮 {mention_user(admin.user)}" for admin in admins]
            bot.reply_to(message, "لیست مدیران:\n" + "\n".join(names), parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: {e}")

    elif lower_text == "جوک":
        bot.reply_to(message, random.choice(JOKES))

    elif lower_text == "راهنما":
        bot.reply_to(message, """
📖 راهنمای ربات:

🔨 **سیک** (با ریپلای) - بن کاربر  
🔓 **حذف سیک** - آزاد کردن  
🔇 **خفه** - سکوت دائمی  
⏱️ **خفه موقت** [ثانیه] - سکوت موقت  
🔊 **حذف خفه** - لغو سکوت  
🗑️ **پاکسازی** [تعداد] - حذف پیام‌ها  
🔒 **قفل** - قفل گروه  
🔓 **باز کردن** - باز کردن  
🎭 **افزودن ادمین** [رمز] - افزودن ادمین  
📋 **ادمین ها** - لیست ادمین‌ها  
🤣 **جوک** - جوک  
📌 **راهنما** - نمایش راهنما
""")

# ==== اجرای برنامه ====
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
