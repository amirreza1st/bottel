import os
import json
import random
from datetime import datetime, timedelta
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_PASSWORD = "1111"

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
    except:
        return False

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    update = types.Update.de_json(request.get_data().decode("utf-8"))
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
➕ newcommand [دستور] = [پاسخ]
➖ deletecommand [دستور]
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
        except:
            send_reply(message, "❗ فرمت صحیح: /newcommand دستور = پاسخ")
    elif message.text.startswith("/deletecommand"):
        try:
            _, key = message.text.split(" ", 1)
            if key.strip() in custom_commands:
                del custom_commands[key.strip()]
                send_reply(message, f"❌ حذف شد: {key.strip()}")
            else:
                send_reply(message, "❗ چنین دستوری وجود ندارد.")
        except:
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

    stats = group_stats.setdefault(chat_id, {'messages': 0, 'users': {}})
    stats['messages'] += 1
    stats['users'][user_id] = stats['users'].get(user_id, 0) + 1
    group_users.setdefault(chat_id, set()).add(user_id)

    lower = text.lower()
    if any(w in lower for w in FILTERED_WORDS):
        bot.delete_message(chat_id, message.message_id)
        send_message(chat_id, f"⚠️ {mention_user(message.from_user)} بی‌ادبی نکن!", parse_mode='Markdown')
        return

    if text in custom_commands:
        send_reply(message, custom_commands[text])
        return

    if text == "گزارش" and message.reply_to_message:
        REPORTS.setdefault(chat_id, []).append(message.reply_to_message)
        send_reply(message, "📩 گزارش ثبت شد. منتظر بررسی ادمین باشید.")
        return

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

    if not is_admin(chat_id, user_id):
        return

    if lower.startswith("ارسال"):
        msg = text[5:].strip()
        success, fail = 0, 0
        for uid in group_users[chat_id]:
            try:
                bot.send_message(uid, f"👑 پیام از {message.chat.title}:

{msg}")
                success += 1
            except:
                fail += 1
        send_reply(message, f"✅ ارسال: {success}
❌ شکست: {fail}")

    elif lower.startswith("سیک") and message.reply_to_message:
        bot.ban_chat_member(chat_id, message.reply_to_message.from_user.id)
        send_reply(message, f"✅ {mention_user(message.reply_to_message.from_user)} بن شد.")

    elif lower.startswith("حذف سیک") and message.reply_to_message:
        bot.unban_chat_member(chat_id, message.reply_to_message.from_user.id)
        send_reply(message, "✅ آزاد شد.")

    elif lower == "خفه" and message.reply_to_message:
        bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=False))
        send_reply(message, "🔇 خفه شد.")

    elif lower == "حذف خفه" and message.reply_to_message:
        bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=True))
        send_reply(message, "🔊 آزاد شد.")

    elif lower.startswith("خفه موقت") and message.reply_to_message:
        try:
            duration = int(lower.split()[2])
            until = datetime.utcnow() + timedelta(seconds=duration)
            bot.restrict_chat_member(chat_id, message.reply_to_message.from_user.id, until, types.ChatPermissions(can_send_messages=False))
            send_reply(message, f"⏱️ خفه موقت شد ({duration} ثانیه)")
        except:
            send_reply(message, "❗ فرمت صحیح: خفه موقت [ثانیه]")

    elif lower.startswith("پاکسازی"):
        try:
            count = int(lower.split()[1])
            for i in range(count):
                bot.delete_message(chat_id, message.message_id - i)
            send_reply(message, f"🗑️ {count} پیام حذف شد.")
        except:
            send_reply(message, "❗ فرمت صحیح: پاکسازی [تعداد]")

    elif lower == "قفل":
        bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False))
        send_reply(message, "🔒 گروه قفل شد.")

    elif lower == "باز کردن":
        bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True))
        send_reply(message, "🔓 گروه باز شد.")

    elif lower.startswith("افزودن ادمین"):
        if lower.split()[-1] == ADMIN_PASSWORD:
            custom_admins.add(user_id)
            send_reply(message, "👮 ادمین شدی.")
        else:
            send_reply(message, "❌ رمز نادرست است.")

    elif lower == "ادمین ها":
        admins = bot.get_chat_administrators(chat_id)
        msg = "
".join(f"👮 {mention_user(a.user)}" for a in admins)
        send_reply(message, msg)

    elif lower == "جوک":
        send_reply(message, random.choice(JOKES))

    elif lower == "امار":
        s = group_stats.get(chat_id)
        if not s:
            send_reply(message, "📊 آماری نیست.")
            return
        reply = f"📊 *آمار گروه:*

📝 پیام‌ها: *{s['messages']}*

👥 کاربران فعال:
"
        for uid, count in sorted(s['users'].items(), key=lambda x: x[1], reverse=True)[:5]:
            try:
                user = bot.get_chat_member(chat_id, uid).user
                reply += f"➤ [{user.first_name}](tg://user?id={user.id}) — {count} پیام
"
            except:
                pass
        send_reply(message, reply)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_report_action(call):
    action, msg_id = call.data.split("_")
    msg_id = int(msg_id)
    try:
        if action == "accept_":
            bot.delete_message(call.message.chat.id, msg_id)
            bot.edit_message_text("✅ پیام حذف شد.", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text("❌ گزارش رد شد.", call.message.chat.id, call.message.message_id)
    except:
        pass

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
