import os
import random
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import Message

# ==== تنظیمات اولیه ====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if TELEGRAM_BOT_TOKEN is None or WEBHOOK_URL is None:
    raise Exception("توکن یا Webhook URL مشخص نشده!")

bot = TeleBot(TELEGRAM_BOT_TOKEN)
ALLOWED_CHAT_ID = -1002648418605
ADMIN_PASSWORD = "1494"
custom_admins = set()
FILTERED_WORDS = ["بد", "زشت"]
JOKES = [
    "🤣 چرا کامپیوتر هیچ‌وقت گرسنه نیست؟ چون همیشه RAM داره!",
    "😆 چرا برنامه‌نویس‌ها از طبیعت خوششون نمیاد؟ چون باگ زیاده!"
]

# ==== Flask app ====
app = Flask(__name__)

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def receive_update():
    update = types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def root():
    return "ربات فعال است ✅"

# ==== توابع و هندلرها ====
def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins) or user_id in custom_admins
    except:
        return False

@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    if message.chat.type == 'private':
        bot.reply_to(message, "Welcome To Moscow 🌙\nDeveloper : @rewhi 👑")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    for new_member in message.new_chat_members:
        bot.send_message(message.chat.id, f"🎉 {new_member.first_name} خوش آمدی!")

@bot.message_handler(func=lambda m: True)
def filter_messages(message: Message):
    if message.chat.id != ALLOWED_CHAT_ID or not message.text:
        return
    for word in FILTERED_WORDS:
        if word in message.text.lower():
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"⚠️ {message.from_user.first_name} لطفاً از الفاظ مناسب استفاده کن.")
            return

@bot.message_handler(commands=['ban'])
def ban_user(message: Message):
    if message.chat.id == ALLOWED_CHAT_ID and is_admin(message.chat.id, message.from_user.id):
        if message.reply_to_message:
            bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "✅ کاربر بن شد.")

@bot.message_handler(commands=['unban'])
def unban_user(message: Message):
    if message.chat.id == ALLOWED_CHAT_ID and is_admin(message.chat.id, message.from_user.id):
        if message.reply_to_message:
            bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "✅ کاربر آزاد شد.")

@bot.message_handler(commands=['mute'])
def mute_user(message: Message):
    if message.chat.id == ALLOWED_CHAT_ID and is_admin(message.chat.id, message.from_user.id):
        if message.reply_to_message:
            bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            bot.reply_to(message, "🔇 کاربر ساکت شد.")

@bot.message_handler(commands=['unmute'])
def unmute_user(message: Message):
    if message.chat.id == ALLOWED_CHAT_ID and is_admin(message.chat.id, message.from_user.id):
        if message.reply_to_message:
            bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                permissions=types.ChatPermissions(can_send_messages=True)
            )
            bot.reply_to(message, "🔊 کاربر آزاد شد.")

@bot.message_handler(commands=['lock'])
def lock_group(message: Message):
    if is_admin(message.chat.id, message.from_user.id):
        bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=False))
        bot.reply_to(message, "🔒 گروه قفل شد.")

@bot.message_handler(commands=['unlock'])
def unlock_group(message: Message):
    if is_admin(message.chat.id, message.from_user.id):
        bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=True))
        bot.reply_to(message, "🔓 گروه باز شد.")

@bot.message_handler(commands=['addadmin'])
def add_admin(message: Message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return
    args = message.text.split()
    if len(args) == 2 and args[1] == ADMIN_PASSWORD:
        custom_admins.add(message.from_user.id)
        bot.reply_to(message, "✅ شما به عنوان ادمین ثبت شدید.")
    else:
        bot.reply_to(message, "❌ رمز نادرست است.")

@bot.message_handler(commands=['admins'])
def list_admins(message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    admins = bot.get_chat_administrators(message.chat.id)
    names = [f"👮 {admin.user.first_name}" for admin in admins]
    bot.reply_to(message, "لیست مدیران:\n" + "\n".join(names))

@bot.message_handler(commands=['help'])
def help_handler(message: Message):
    help_text = """
📖 راهنمای ربات:

🔨 /ban - بن کاربر (با ریپلای)
🔓 /unban - آن‌بن کاربر
🔇 /mute - سکوت کاربر
🔊 /unmute - لغو سکوت
🔒 /lock - قفل گروه
🔓 /unlock - باز کردن گروه
🎭 /addadmin [رمز] - افزودن ادمین
📋 /admins - لیست ادمین‌ها
🤣 /joke - جوک بامزه
📌 /help - راهنما
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['joke'])
def joke_handler(message: Message):
    bot.reply_to(message, random.choice(JOKES))

# ==== شروع برنامه ====
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
