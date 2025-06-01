import os
import random
from datetime import datetime, timedelta
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_PASSWORD = "111166"

if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
    raise Exception("توکن یا Webhook URL مشخص نشده!")

bot = TeleBot(TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

custom_admins = set()
custom_commands = {}
FILTERED_WORDS = ["کص", "کوص", "ننت", "مادرت", "مامانت", "ننه", "جنده", "کونده", "کصده", "خارت", "خواهرتو", "کوس", "ابجیتو", "کونتو", "لینک"]
JOKES = [
    "🤣 چرا کامپیوتر هیچ‌وقت گرسنه نیست؟ چون همیشه RAM داره!",
    "😆 چرا برنامه‌نویس‌ها از طبیعت خوششون نمیاد؟ چون باگ زیاده!",
    "یه روز گربه‌هه گفت میو، خرگوشه هم گفت مهندس شما؟",
    "‏به یکی گفتم: چقد خوشگلی!! گفت: چشات قشنگ میبینه. بعداً فهمیدم راست میگه 😐",
]

group_users = {}
group_stats = {}
REPORTS = {}
FINAL_IMAGE_URL = "https://uploadkon.ir/uploads/96a601_25photo18968523702.jpg"

def send_message(chat_id, text, reply_to_message_id=None, parse_mode='Markdown'):
    return bot.send_message(chat_id, text, reply_to_message_id=reply_to_message_id, parse_mode=parse_mode)

def send_message_with_image(chat_id, text, reply_to_message_id=None, parse_mode='Markdown'):
    return bot.send_photo(chat_id, FINAL_IMAGE_URL, caption=text, reply_to_message_id=reply_to_message_id, parse_mode=parse_mode)

def send_reply(message, text, parse_mode='Markdown'):
    return send_message(message.chat.id, text, reply_to_message_id=message.message_id, parse_mode=parse_mode)

def mention_user(user):
    return f"[{user.first_name}](tg://user?id={user.id})"

def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return user_id in custom_admins or any(admin.user.id == user_id for admin in admins)
    except Exception:
        return False

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "ربات فعال است ✅"

@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    if message.chat.type == 'private':
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📚 راهنما", callback_data="help"))
        bot.send_photo(message.chat.id, FINAL_IMAGE_URL,
            caption="""🌙 *Welcome To Moscow Night* 🌙

👑 Developer : @rewhi
برای شروع از دکمه زیر استفاده کنید.""",
            reply_markup=kb, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data == "help")
def callback_help(call):
    help_text = """
✨ *راهنمای کاربر :*

🚫 سیک - بن کاربر (ریپلی)
♻️ حذف سیک - آزاد کردن کاربر (ریپلی)
🔕 خفه - سکوت دائم (ریپلی)
🔕 خفه موقت [ثانیه] (ریپلی)
🔊 حذف خفه - لغو سکوت (ریپلی)
🗑 پاکسازی [تعداد]
🔐 قفل / 🔓 باز کردن گروه
🧸 افزودن ادمین [رمز]
🗂 ادمین ها - لیست ادمین‌ها
😂 جوک - گفتن جوک تصادفی
📊 امار - نمایش آمار
📩 گزارش - ارسال گزارش با ریپلی
📥 بررسی گزارش‌ها (فقط ادمین)
    """
    bot.send_message(call.message.chat.id, help_text.strip(), parse_mode='Markdown')

@bot.message_handler(commands=['newcommand', 'deletecommand'])
def command_handler(message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return send_reply(message, "⛔ فقط ادمین‌ها دسترسی دارند.")

    if message.text.startswith("/newcommand"):
        try:
            _, pair = message.text.split(" ", 1)
            key, val = pair.split("=", 1)
            custom_commands[key.strip()] = val.strip()
            send_reply(message, f"✅ دستور جدید افزوده شد: {key.strip()}")
        except Exception:
            send_reply(message, "❗ فرمت صحیح: /newcommand دستور = پاسخ")
    elif message.text.startswith("/deletecommand"):
        try:
            _, key = message.text.split(" ", 1)
            if key.strip() in custom_commands:
                del custom_commands[key.strip()]
                send_reply(message, f"❌ حذف شد: {key.strip()}")
            else:
                send_reply(message, "❗ چنین دستوری وجود ندارد.")
        except Exception:
            send_reply(message, "❗ فرمت صحیح: /deletecommand دستور")

@bot.message_handler(content_types=['new_chat_members'])
def welcome(message: Message):
    for member in message.new_chat_members:
        send_message(message.chat.id, f"🤤 ممبر جدید {mention_user(member)}!", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""

    # آمار پیام‌ها و کاربران فعال
    stats = group_stats.setdefault(chat_id, {'messages': 0, 'users': {}})
    stats['messages'] += 1
    stats['users'][user_id] = stats['users'].get(user_id, 0) + 1
    group_users.setdefault(chat_id, set()).add(user_id)

    lower = text.lower()

    # فیلتر کلمات رکیک
    if any(w in lower for w in FILTERED_WORDS):
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass
        send_message(chat_id, f"⚠️ {mention_user(message.from_user)} بی‌ادبی نکن!", parse_mode='Markdown')
        return

    # دستورهای سفارشی
    if text in custom_commands:
        send_reply(message, custom_commands[text])
        return

    # ثبت گزارش
    if text == "گزارش" and message.reply_to_message:
        REPORTS.setdefault(chat_id, []).append(message.reply_to_message)
        send_reply(message, "📩 گزارش ثبت شد. منتظر بررسی ادمین باشید.")
        return

    # بررسی گزارش‌ها توسط ادمین‌ها
    if text == "بررسی گزارش‌ها" and is_admin(chat_id, user_id):
        reports = REPORTS.get(chat_id, [])
        if not reports:
            send_reply(message, "📭 گزارشی موجود نیست.")
            return
        for rep in reports:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ تایید", callback_data=f"accept_{rep.message_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{rep.message_id}")
            )
            bot.send_message(chat_id, f"""گزارش برای {mention_user(rep.from_user)}:
{rep.text}""", reply_markup=kb, parse_mode="Markdown")
        REPORTS[chat_id] = []
        return

    # فقط ادمین‌ها مجاز به دستورات زیر هستند
    if not is_admin(chat_id, user_id):
        return

    # دستورات ادمینی
    if lower.startswith("ارسال "):
        msg = text[5:].strip()
        success, fail = 0, 0
        for uid in group_users.get(chat_id, []):
            try:
                bot.send_message(uid, f"""👑 پیام از {message.chat.title}:

{msg}""")
                success += 1
            except Exception:
                fail += 1
        send_reply(message, f"""✅ ارسال: {success}
❌ شکست: {fail}""")

    elif lower.startswith("سیک") and message.reply_to_message:
        try:
            bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
            send_reply(message, f"✅ {mention_user(message.reply_to_message.from_user)} بن شد.")
        except Exception:
            send_reply(message, "❗ خطا در بن کردن کاربر.")

    elif lower.startswith("حذف سیک") and message.reply_to_message:
        try:
            bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
            send_reply(message, "✅ آزاد شد.")
        except Exception:
            send_reply(message, "❗ خطا در آزاد کردن کاربر.")

    elif lower == "خفه" and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=False))
            send_reply(message, "🔇 خفه شد.")
        except Exception:
            send_reply(message, "❗ خطا در سکوت دائم.")

    elif lower == "حذف خفه" and message.reply_to_message:
        try:
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=True))
            send_reply(message, "🔊 آزاد شد.")
        except Exception:
            send_reply(message, "❗ خطا در لغو سکوت.")

    elif lower.startswith("خفه موقت") and message.reply_to_message:
        try:
            parts = lower.split()
            duration = int(parts[2])
            until = datetime.utcnow() + timedelta(seconds=duration)
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, until_date=until, permissions=types.ChatPermissions(can_send_messages=False))
            send_reply(message, f"⏱️ خفه موقت شد ({duration} ثانیه)")
        except Exception:
            send_reply(message, "❗ فرمت صحیح: خفه موقت [ثانیه]")

    elif lower.startswith("پاکسازی"):
        try:
            count = int(lower.split()[1])
            for i in range(count):
                bot.delete_message(chat_id, message.message_id - i)
            send_reply(message, f"🗑️ {count} پیام حذف شد.")
        except Exception:
            send_reply(message, "❗ فرمت صحیح: پاکسازی [تعداد]")

    elif lower == "قفل":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False))
            send_reply(message, "🔒 گروه قفل شد.")
        except Exception:
            send_reply(message, "❗ خطا در قفل کردن گروه.")

    elif lower == "باز کردن":
        try:
            bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True))
            send_reply(message, "🔓 گروه باز شد.")
        except Exception:
            send_reply(message, "❗ خطا در باز کردن گروه.")

    elif lower.startswith("افزودن ادمین"):
        if lower.split()[-1] == ADMIN_PASSWORD:
            custom_admins.add(user_id)
            send_reply(message, "👮 ادمین شدی.")
        else:
            send_reply(message, "❌ رمز نادرست است.")

    elif lower == "ادمین ها":
        try:
            admins = bot.get_chat_administrators(chat_id)
            msg = "\n".join(f"👮 {mention_user(a.user)}" for a in admins)
            send_reply(message, msg)
        except Exception:
            send_reply(message, "❗ خطا در دریافت لیست ادمین‌ها.")

    elif lower == "جوک":
        send_reply(message, random.choice(JOKES))

    elif lower == "امار":
        s = group_stats.get(chat_id)
        if not s:
            send_reply(message, "📊 آماری نیست.")
            return
        reply = f"""📊 *آمار گروه:*

📝 پیام‌ها: *{s['messages']}*

👥 کاربران فعال:
"""
        for uid, count in sorted(s['users'].items(), key=lambda x: x[1], reverse=True):
            reply += f"- [{uid}](tg://user?id={uid}): {count} پیام\n"
        send_reply(message, reply)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def callback_report_handler(call):
    try:
        action, msg_id = call.data.split("_", 1)
        chat_id = call.message.chat.id
        # فقط ادمین‌ها می‌توانند این کار را انجام دهند
        if not is_admin(chat_id, call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ فقط ادمین‌ها مجاز هستند.")
            return

        # حذف پیام گزارش‌شده یا انجام اقدامات لازم
        msg_id = int(msg_id)
        if action == "accept":
            bot.delete_message(chat_id, msg_id)
            bot.answer_callback_query(call.id, "✅ پیام حذف شد.")
        elif action == "reject":
            bot.answer_callback_query(call.id, "❌ رد شد.")
    except Exception:
        bot.answer_callback_query(call.id, "❗ خطا در پردازش گزارش.")

if __name__ == "__main__":
    # تنظیم webhook
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/" + TELEGRAM_BOT_TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
