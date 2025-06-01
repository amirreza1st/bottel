import os
import random
from telebot import TeleBot, types
from telebot.types import Message

# دریافت توکن از متغیر محیطی
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print("DEBUG: TELEGRAM_BOT_TOKEN =", TELEGRAM_BOT_TOKEN)

if TELEGRAM_BOT_TOKEN is None:
    raise Exception("TELEGRAM_BOT_TOKEN is None! Set your environment variable correctly.")

bot = TeleBot(token=TELEGRAM_BOT_TOKEN)

# شناسه گروه مجاز (آن را با آی‌دی گروه خود جایگزین کنید)
ALLOWED_CHAT_ID = -1002648418605

# رمز عبور افزودن ادمین
ADMIN_PASSWORD = "1494"
custom_admins = set()

# لیست کلمات فیلتر شده
FILTERED_WORDS = ["بد", "زشت"]

# لیست جوک‌ها
JOKES = [
    "🤣 چرا کامپیوتر هیچ‌وقت گرسنه نیست؟ چون همیشه RAM داره!",
    "😆 چرا برنامه‌نویس‌ها از طبیعت خوششون نمیاد؟ چون باگ زیاده!"
]

# بررسی ادمین بودن

def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins) or user_id in custom_admins
    except:
        return False

# پیام استارت در پی‌وی
@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    if message.chat.type == 'private':
        bot.reply_to(message, """Welcome To Moscow 🌙
Developer : @rewhi 👑""")

# پیام خوش‌آمد
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    for new_member in message.new_chat_members:
        bot.send_message(message.chat.id, f"🎉 {new_member.first_name} خوش آمدی!")

# فیلتر کلمات
@bot.message_handler(func=lambda m: True)
def filter_messages(message: Message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return
    for word in FILTERED_WORDS:
        if word in message.text.lower():
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"⚠️ {message.from_user.first_name} لطفاً از الفاظ مناسب استفاده کن.")
            return

# بن
@bot.message_handler(commands=['ban'])
def ban_user(message: Message):
    if message.chat.id == ALLOWED_CHAT_ID and is_admin(message.chat.id, message.from_user.id):
        if message.reply_to_message:
            bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "✅ کاربر بن شد.")

# آن‌بن
@bot.message_handler(commands=['unban'])
def unban_user(message: Message):
    if message.chat.id == ALLOWED_CHAT_ID and is_admin(message.chat.id, message.from_user.id):
        if message.reply_to_message:
            bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message, "✅ کاربر آزاد شد.")

# سکوت
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

# لغو سکوت
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

# قفل گروه
@bot.message_handler(commands=['lock'])
def lock_group(message: Message):
    if is_admin(message.chat.id, message.from_user.id):
        bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=False))
        bot.reply_to(message, "🔒 گروه قفل شد.")

# باز کردن گروه
@bot.message_handler(commands=['unlock'])
def unlock_group(message: Message):
    if is_admin(message.chat.id, message.from_user.id):
        bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=True))
        bot.reply_to(message, "🔓 گروه باز شد.")

# افزودن ادمین با رمز
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

# لیست ادمین‌ها
@bot.message_handler(commands=['admins'])
def list_admins(message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    admins = bot.get_chat_administrators(message.chat.id)
    names = [f"👮 {admin.user.first_name}" for admin in admins]
    bot.reply_to(message, """لیست مدیران:
""" + "\n".join(names))

# راهنما
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

# جوک
@bot.message_handler(commands=['joke'])
def joke_handler(message: Message):
    bot.reply_to(message, random.choice(JOKES))



@bot.message_handler(func=lambda message: True)
def test_all_messages(message: Message):
    print(f"[DEBUG] Received message in chat {message.chat.id}: {message.text}")
    bot.reply_to(message, "✅ پیام شما دریافت شد.")

# شروع بی‌نهایت
bot.infinity_polling()
