import os
from dotenv import load_dotenv
from telebot import TeleBot, types
from telebot.types import Message, ChatPermissions
import re

# بارگذاری متغیرهای محیطی
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

bot = TeleBot(token=TELEGRAM_BOT_TOKEN)

# متغیرهای اصلی
admins = set()
bad_words = {"لعنتی", "بد"}
locks = {"link": False, "photo": False, "video": False}

# خوش‌آمدگویی کاربران جدید
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_user(message):
    for user in message.new_chat_members:
        bot.send_message(message.chat.id, f"خوش اومدی {user.first_name} 🌟")

# پاسخ به منشن
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and f"@{bot.get_me().username}" in message.text)
def reply_to_mention(message: Message):
    bot.reply_to(message, "صدات رسید 📣 چه کاری از دستم برمیاد؟")

# بن کاربر
@bot.message_handler(commands=['ban'])
def ban_user(message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.kick_chat_member(message.chat.id, user_id)
        bot.reply_to(message, "کاربر بن شد ❌")

# آن‌بن کاربر
@bot.message_handler(commands=['unban'])
def unban_user(message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.unban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, "کاربر آزاد شد ✅")

# سکوت کاربر
@bot.message_handler(commands=['mute'])
def mute_user(message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
        bot.reply_to(message, "کاربر در سکوت قرار گرفت 🔇")

# لغو سکوت کاربر
@bot.message_handler(commands=['unmute'])
def unmute_user(message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True)
        bot.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
        bot.reply_to(message, "سکوت کاربر برداشته شد 🔊")

# قفل/باز کردن محتوا
@bot.message_handler(commands=['lock', 'unlock'])
def toggle_lock(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "مثال: /lock link یا /unlock photo")
        return
    cmd, item = parts[0], parts[1]
    if item not in locks:
        bot.reply_to(message, f"نوع قفل نامعتبر است: {item}")
        return
    locks[item] = True if cmd == '/lock' else False
    bot.reply_to(message, f"{'قفل شد 🔐' if cmd == '/lock' else 'باز شد 🔓'}: {item}")

# حذف محتوای قفل شده
@bot.message_handler(content_types=['text', 'photo', 'video'])
def content_filter(message: Message):
    if message.chat.type not in ['group', 'supergroup']:
        return
    if locks['link'] and message.text and re.search(r"http[s]?://", message.text):
        bot.delete_message(message.chat.id, message.message_id)
    if locks['photo'] and message.content_type == 'photo':
        bot.delete_message(message.chat.id, message.message_id)
    if locks['video'] and message.content_type == 'video':
        bot.delete_message(message.chat.id, message.message_id)

# فیلتر کلمات نامناسب
@bot.message_handler(func=lambda m: any(word in m.text.lower() for word in bad_words))
def filter_bad_words(message: Message):
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, "🚫 لطفاً از کلمات مناسب استفاده کنید")

# گزارش به مدیر
@bot.message_handler(commands=['report'])
def report_to_admin(message: Message):
    if message.reply_to_message:
        reported_user = message.reply_to_message.from_user
        report_message = (
            f"📢 گزارش جدید از گروه:\n"
            f"گزارش‌دهنده: @{message.from_user.username}\n"
            f"کاربر گزارش‌شده: @{reported_user.username}\n"
            f"متن پیام: {message.reply_to_message.text}"
        )
        bot.send_message(OWNER_ID, report_message)
        bot.reply_to(message, "گزارش شما به مدیر ارسال شد ✅")

# افزودن ادمین با رمز
@bot.message_handler(commands=['admin'])
def make_admin(message: Message):
    parts = message.text.split()
    if len(parts) == 2 and parts[1] == ADMIN_PASSWORD:
        admins.add(message.from_user.id)
        bot.reply_to(message, "شما اکنون ادمین هستید ✅")
    else:
        bot.reply_to(message, "رمز اشتباه است ❌")

# لیست مدیران
@bot.message_handler(commands=['admins'])
def list_admins(message: Message):
    if not admins:
        bot.reply_to(message, "هیچ مدیری ثبت نشده است.")
    else:
        mention_list = '\n'.join([f"[Admin](tg://user?id={aid})" for aid in admins])
        bot.send_message(message.chat.id, f"👮‍♂️ لیست مدیران:\n{mention_list}", parse_mode="Markdown")

# پیام خصوصی به مدیر
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def forward_to_owner(message: Message):
    if OWNER_ID:
        private_message = (
            f"پیام جدید از {message.from_user.first_name}:\n"
            f"{message.text}"
        )
        bot.send_message(OWNER_ID, private_message)
        bot.reply_to(message, "پیام شما به مدیر ارسال شد ✅")

# اجرای ربات
bot.infinity_polling()
