import os
import random
from datetime import datetime, timedelta
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# دریافت توکن و آدرس وبهوک از متغیرهای محیطی
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_PASSWORD = "111166"

if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
    raise Exception("توکن یا آدرس وبهوک تعریف نشده است!")

bot = TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# ادمین‌های سفارشی به همراه مالک ربات
custom_admins = {7590426649}  # این ایدی مالک و فول ادمین ربات است

# دستورهای سفارشی قابل افزودن توسط ادمین‌ها
custom_commands = {}

# کلمات فیلتر شده برای حذف پیام‌های توهین‌آمیز
FILTERED_WORDS = [
    "کص", "کوص", "ننت", "مادرت", "مامانت", "ننه", "جنده", 
    "کونده", "کصده", "خارت", "خواهرتو", "کوس", "ابجیتو", 
    "کونتو", "لینک"
]

# جوک‌های آماده برای ارسال به درخواست کاربران
JOKES = [
    "🤣 چرا کامپیوتر هیچ‌وقت گرسنه نیست؟ چون همیشه RAM داره!",
    "😆 چرا برنامه‌نویس‌ها از طبیعت خوششون نمیاد؟ چون باگ زیاده!",
    "یه روز گربه‌هه گفت میو، خرگوشه هم گفت مهندس شما؟",
    "‏به یکی گفتم: چقد خوشگلی!! گفت: چشات قشنگ میبینه. بعداً فهمیدم راست میگه 😐",
]

# ذخیره کاربران گروه‌ها و آمار پیام‌ها
group_users = {}
group_stats = {}

# ذخیره گزارش‌های ارسال‌شده در گروه‌ها
REPORTS = {}

# تصویری که در برخی پاسخ‌ها ارسال می‌شود
FINAL_IMAGE_URL = "https://uploadkon.ir/uploads/96a601_25photo18968523702.jpg"

def send_message(chat_id, text, reply_to_message_id=None, parse_mode='Markdown'):
    """ارسال پیام متنی به چت"""
    return bot.send_message(chat_id, text, reply_to_message_id=reply_to_message_id, parse_mode=parse_mode)

def send_message_with_image(chat_id, text, reply_to_message_id=None, parse_mode='Markdown'):
    """ارسال پیام همراه عکس"""
    return bot.send_photo(chat_id, FINAL_IMAGE_URL, caption=text, reply_to_message_id=reply_to_message_id, parse_mode=parse_mode)

def send_reply(message, text, parse_mode='Markdown'):
    """ارسال پاسخ به پیام کاربر"""
    return send_message(message.chat.id, text, reply_to_message_id=message.message_id, parse_mode=parse_mode)

def mention_user(user):
    """ساخت متن منشن با نام کاربر"""
    return f"[{user.first_name}](tg://user?id={user.id})"

def is_admin(chat_id, user_id):
    """بررسی اینکه آیا کاربر ادمین گروه یا ادمین سفارشی است"""
    try:
        admins = bot.get_chat_administrators(chat_id)
        return user_id in custom_admins or any(admin.user.id == user_id for admin in admins)
    except Exception:
        return False

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    """دریافت آپدیت از تلگرام از طریق وبهوک"""
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    """پاسخ ساده برای تست سلامت ربات"""
    return "ربات با موفقیت فعال است ✅"

@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    """دستور شروع در چت خصوصی - ارسال لینک ارتباط با ما"""
    if message.chat.type == 'private':
        text = """🌟 سلام! برای ارتباط با ما و دریافت راهنمای کامل، لطفاً روی لینک زیر کلیک کنید:

[📬 ارتباط با ما](https://t.me/rewhi)"""
        bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_handler(message: Message):
    """دستور راهنما با توضیح کامل و روان"""
    help_text = """
✨ *راهنمای کامل استفاده از ربات:*

🚫 *سیک* - بن کردن کاربر (ریپلای کنید)
♻️ *حذف سیک* - آزاد کردن کاربر از بن (ریپلای کنید)
🔕 *خفه* - سکوت دائم کاربر (ریپلای کنید)
⏱ *خفه موقت [ثانیه]* - سکوت موقت به مدت مشخص (ریپلای کنید)
🔊 *حذف خفه* - لغو سکوت کاربر (ریپلای کنید)
🗑 *پاکسازی [تعداد]* - حذف تعداد مشخصی پیام از چت
🔐 *قفل* - قفل کردن گروه (عدم ارسال پیام توسط اعضا)
🔓 *باز کردن* - باز کردن گروه برای ارسال پیام
🧸 *افزودن ادمین [رمز]* - افزودن خود به لیست ادمین‌ها
🗂 *ادمین‌ها* - نمایش لیست ادمین‌های گروه
😂 *جوک* - ارسال یک جوک تصادفی برای اعضا
📊 *آمار* - نمایش آمار پیام‌ها و کاربران فعال
📩 *گزارش* - ارسال گزارش برای پیام ریپلای‌شده
📥 *بررسی گزارش‌ها* - مشاهده و مدیریت گزارش‌ها (فقط برای ادمین‌ها)
"""
    send_reply(message, help_text.strip())

@bot.message_handler(commands=['newcommand', 'deletecommand'])
def command_handler(message: Message):
    """افزودن یا حذف دستورهای سفارشی توسط ادمین‌ها"""
    if not is_admin(message.chat.id, message.from_user.id):
        return send_reply(message, "⛔ فقط ادمین‌های گروه مجاز به این کار هستند.")

    if message.text.startswith("/newcommand"):
        try:
            _, pair = message.text.split(" ", 1)
            key, val = pair.split("=", 1)
            custom_commands[key.strip()] = val.strip()
            send_reply(message, f"✅ دستور جدید با موفقیت اضافه شد:\n`{key.strip()}`")
        except Exception:
            send_reply(message, "❗ لطفاً از فرمت زیر استفاده کنید:\n`/newcommand دستور = پاسخ`")
    elif message.text.startswith("/deletecommand"):
        try:
            _, key = message.text.split(" ", 1)
            if key.strip() in custom_commands:
                del custom_commands[key.strip()]
                send_reply(message, f"❌ دستور `{key.strip()}` با موفقیت حذف شد.")
            else:
                send_reply(message, "❗ چنین دستوری یافت نشد.")
        except Exception:
            send_reply(message, "❗ لطفاً از فرمت زیر استفاده کنید:\n`/deletecommand دستور`")

@bot.message_handler(content_types=['new_chat_members'])
def welcome(message: Message):
    """خوش‌آمدگویی به اعضای جدید گروه"""
    for member in message.new_chat_members:
        send_message(message.chat.id, f"🎉 به جمع ما خوش آمدی {mention_user(member)}! امیدواریم اوقات خوبی داشته باشی.", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group(message: Message):
    """مدیریت پیام‌های گروه، فیلتر کلمات، دستورات و گزارش‌ها"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""

    # به‌روزرسانی آمار پیام‌ها و کاربران فعال
    stats = group_stats.setdefault(chat_id, {'messages': 0, 'users': {}})
    stats['messages'] += 1
    stats['users'][user_id] = stats['users'].get(user_id, 0) + 1
    group_users.setdefault(chat_id, set()).add(user_id)

    lower = text.lower()

    # حذف پیام‌های حاوی کلمات رکیک و هشدار به کاربر
    if any(bad_word in lower for bad_word in FILTERED_WORDS):
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass
        send_message(chat_id, f"⚠️ {mention_user(message.from_user)} لطفاً ادب را رعایت کنید!", parse_mode='Markdown')
        return

    # پاسخ به دستورات سفارشی
    if text in custom_commands:
        send_reply(message, custom_commands[text])
        return

    # ثبت گزارش برای پیام ریپلای‌شده
    if text == "گزارش" and message.reply_to_message:
        REPORTS.setdefault(chat_id, []).append(message.reply_to_message)
        send_reply(message, "📩 گزارش شما ثبت شد. ادمین‌ها در حال بررسی هستند.")
        return

    # مشاهده گزارش‌ها توسط ادمین‌ها
    if text == "بررسی گزارش‌ها" and is_admin(chat_id, user_id):
        reports = REPORTS.get(chat_id, [])
        if not reports:
            send_reply(message, "📭 گزارش جدیدی وجود ندارد.")
            return
        for rep in reports:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ تایید و حذف پیام", callback_data=f"accept_{rep.message_id}"),
                InlineKeyboardButton("❌ رد گزارش", callback_data=f"reject_{rep.message_id}")
            )
            bot.send_message(chat_id, f"""گزارش برای پیام از طرف {mention_user(rep.from_user)}:
{rep.text}""", reply_markup=kb, parse_mode="Markdown")
        REPORTS[chat_id] = []
        return

    # دستورات مدیریتی (فقط برای ادمین‌ها)
    if not is_admin(chat_id, user_id):
        return

    # ارسال پیام به همه اعضای گروه
    if lower.startswith("ارسال "):
        msg = text[5:].strip()
        success, fail = 0, 0
        for uid in group_users.get(chat_id, []):
            try:
                bot.send_message(uid, f"""👑 پیام جدید از گروه {message.chat.title}:

{msg}""")
                success += 1
            except Exception:
                fail += 1
        send_reply(message, f"""✅ پیام با موفقیت به {success} نفر ارسال شد.
⚠️ ارسال به {fail} نفر ناموفق بود.""")

    # بن کردن کاربر (ریپلای شده)
    elif lower.startswith("سیک") and message.reply_to_message:
        try:
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            send_reply(message, f"✅ {mention_user(message.reply_to_message.from_user)} از گروه بن شد.")
        except Exception:
            send_reply(message, "❗ خطا در بن کردن کاربر. دوباره تلاش کنید.")

    # آزاد کردن کاربر از بن (ریپلای شده)
    elif lower.startswith("حذف سیک") and message.reply_to_message:
        try:
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            send_reply(message, "✅ کاربر آزاد شد.")
        except Exception:
            send_reply(message, "❗ خطا در آزادسازی کاربر.")

    # سکوت دائم کاربر (ریپلای شده)
    elif lower == "خفه" and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id,
                                    permissions=types.ChatPermissions(can_send_messages=False))
            send_reply(message, "🔇 کاربر به سکوت دائم فرو رفت.")
        except Exception:
            send_reply(message, "❗ خطا در اعمال سکوت دائم.")

    # لغو سکوت (ریپلای شده)
    elif lower == "حذف خفه" and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id,
                                    permissions=types.ChatPermissions(can_send_messages=True))
            send_reply(message, "🔊 سکوت کاربر برداشته شد.")
        except Exception:
            send_reply(message, "❗ خطا در لغو سکوت.")

    # سکوت موقت (ریپلای شده)
    elif lower.startswith("خفه موقت") and message.reply_to_message:
        try:
            parts = lower.split()
            duration = int(parts[2])
            until = datetime.utcnow() + timedelta(seconds=duration)
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id,
                                    until_date=until,
                                    permissions=types.ChatPermissions(can_send_messages=False))
            send_reply(message, f"⏱️ کاربر به مدت {duration} ثانیه سکوت کرد.")
        except Exception:
            send_reply(message, "❗ لطفاً فرمت را به شکل زیر وارد کنید:\n`خفه موقت [ثانیه]`")

    # حذف تعداد مشخصی پیام از گروه
    elif lower.startswith("پاکسازی"):
        try:
            count = int(lower.split()[1])
            for i in range(count):
                bot.delete_message(chat_id, message.message_id - i)
            send_reply(message, f"🗑️ تعداد {count} پیام با موفقیت
