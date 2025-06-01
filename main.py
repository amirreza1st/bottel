import os
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import Message

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize bot
bot = TeleBot(token=TELEGRAM_BOT_TOKEN)

# حافظه موقت برای نگهداری حالت ارسال پیام ناشناس
anon_targets = {}

@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    chat_id = message.chat.id
    args = message.text.split()
    
    if len(args) > 1:
        # پیام ناشناس برای کاربر خاص
        target_user_id = args[1]
        anon_targets[chat_id] = target_user_id
        bot.send_message(chat_id, "✉️ پیامت را بنویس تا به صورت ناشناس ارسال شود:")
    else:
        bot.send_message(chat_id, f"سلام {message.from_user.first_name}!\n"
                                  f"برای دریافت پیام ناشناس، لینک زیر را برای دوستانت بفرست:\n"
                                  f"https://t.me/{bot.get_me().username}?start={chat_id}")

@bot.message_handler(commands=['myid'])
def my_id(message: Message):
    bot.reply_to(message, f"🆔 آیدی شما: `{message.chat.id}`", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_or_forward(message: Message):
    chat_id = message.chat.id
    if chat_id in anon_targets:
        target_id = anon_targets.pop(chat_id)
        bot.send_message(int(target_id), f"📩 یک پیام ناشناس برایت آمده:\n\n{message.text}")
        bot.send_message(chat_id, "✅ پیام ناشناس شما ارسال شد.")
    else:
        bot.send_message(chat_id, "📬 من یک ربات پیام ناشناس هستم. برای دریافت لینک ناشناس از /start استفاده کن.")

bot.infinity_polling()
