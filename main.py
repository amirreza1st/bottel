import os
from telebot import TeleBot
from telebot.types import Message

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("DEBUG: TELEGRAM_BOT_TOKEN =", TELEGRAM_BOT_TOKEN)

if TELEGRAM_BOT_TOKEN is None:
    raise Exception("TELEGRAM_BOT_TOKEN is None! Set your environment variable correctly.")

bot = TeleBot(token=TELEGRAM_BOT_TOKEN)

# لیست کلمات فیلتر شده
FILTERED_WORDS = ["بد", "زشت", "نفرت"]  # نمونه کلمات فیلتر شده

# وضعیت قفل‌ها (True یعنی قفل است)
lock_settings = {
    "links": False,
    "photos": False,
    "videos": False
}

# ---------------- پیام /start در پیوی ----------------
@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    if message.chat.type == "private":
        bot.send_message(message.chat.id, "سلام! به ربات خوش آمدید. هر سوالی داشتید بپرسید!")

# ---------------- پیام خوش‌آمدگویی کاربر جدید ----------------
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message: Message):
    for new_user in message.new_chat_members:
        bot.send_message(message.chat.id, f"سلام {new_user.first_name} خوش آمدی به گروه!")

# ---------------- فیلتر کلمات ----------------
@bot.message_handler(func=lambda m: True, content_types=['text'])
def filter_bad_words(message: Message):
    text_lower = message.text.lower()
    for bad_word in FILTERED_WORDS:
        if bad_word in text_lower:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"{message.from_user.first_name}، لطفا از کلمات نامناسب استفاده نکنید!")
            # گزارش به مدیر
            for admin_id in ADMIN_IDS:
                bot.send_message(admin_id, f"کاربر {message.from_user.id} پیام نامناسب فرستاد:\n{message.text}")
            return

# ---------------- بن کردن کاربر ----------------
@bot.message_handler(commands=['ban'])
def ban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "شما دسترسی لازم را ندارید.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای بن کردن، لطفا پیام کاربر را جواب دهید.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        bot.kick_chat_member(message.chat.id, user_id)
        bot.send_message(message.chat.id, f"کاربر {user_id} بن شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا: {e}")

# ---------------- آن‌بن کردن کاربر ----------------
@bot.message_handler(commands=['unban'])
def unban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "شما دسترسی لازم را ندارید.")
        return
    if len(message.text.split()) < 2:
        bot.reply_to(message, "برای آن‌بن کردن، شناسه کاربر را وارد کنید: /unban user_id")
        return
    try:
        user_id = int(message.text.split()[1])
        bot.unban_chat_member(message.chat.id, user_id)
        bot.send_message(message.chat.id, f"کاربر {user_id} آن‌بن شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا: {e}")

# ---------------- سکوت کردن کاربر ----------------
@bot.message_handler(commands=['mute'])
def mute_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "شما دسترسی لازم را ندارید.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای سکوت کردن، لطفا پیام کاربر را جواب دهید.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.send_message(message.chat.id, f"کاربر {user_id} سکوت داده شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا: {e}")

# ---------------- لغو سکوت کاربر ----------------
@bot.message_handler(commands=['unmute'])
def unmute_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "شما دسترسی لازم را ندارید.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای لغو سکوت، لطفا پیام کاربر را جواب دهید.")
        return
    user_id = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        bot.send_message(message.chat.id, f"کاربر {user_id} سکوت برداشته شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا: {e}")

# ---------------- قفل/باز کردن انواع محتوا ----------------
@bot.message_handler(commands=['lock', 'unlock'])
def lock_unlock_content(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "شما دسترسی لازم را ندارید.")
        return

    cmd = message.text.split()
    if len(cmd) < 3:
        bot.reply_to(message, "استفاده: /lock|unlock content_type (links/photos/videos)")
        return

    action = cmd[0][1:]  # lock یا unlock
    content_type = cmd[2].lower()

    if content_type not in lock_settings:
        bot.reply_to(message, "نوع محتوا باید یکی از links, photos, videos باشد.")
        return

    lock_settings[content_type] = (action == "lock")
    status = "قفل شد" if lock_settings[content_type] else "باز شد"
    bot.send_message(message.chat.id, f"{content_type} {status}")

# ---------------- حذف پیام‌های قفل شده ----------------
@bot.message_handler(func=lambda m: True)
def delete_locked_content(message: Message):
    if lock_settings["links"]:
        if message.entities:
            for entity in message.entities:
                if entity.type == "url":
                    bot.delete_message(message.chat.id, message.message_id)
                    return
    if lock_settings["photos"] and message.content_type == "photo":
        bot.delete_message(message.chat.id, message.message_id)
        return
    if lock_settings["videos"] and message.content_type == "video":
        bot.delete_message(message.chat.id, message.message_id)
        return

# ---------------- لیست مدیران ----------------
@bot.message_handler(commands=['admins'])
def list_admins(message: Message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "این دستور فقط در گروه‌ها کار می‌کند.")
        return
    admins = bot.get_chat_administrators(message.chat.id)
    text = "لیست مدیران گروه:\n"
    for admin in admins:
        user = admin.user
        text += f"- {user.first_name} (ID: {user.id})\n"
    bot.send_message(message.chat.id, text)

# ---------------- ادمین کردن کاربر با رمز ----------------
# برای سادگی، فرض کنیم ادمین کردن فقط با ارسال دستور /promote user_id password انجام شود
@bot.message_handler(commands=['promote'])
def promote_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "شما دسترسی لازم را ندارید.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "استفاده: /promote user_id password")
        return
    try:
        user_id = int(parts[1])
        password = parts[2]
        if password != ADMIN_PASSWORD:
            bot.reply_to(message, "رمز اشتباه است.")
            return
        bot.promote_chat_member(
            message.chat.id,
            user_id,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=True
        )
        bot.send_message(message.chat.id, f"کاربر {user_id} ادمین شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا: {e}")


bot.infinity_polling()


bot.infinity_polling()
