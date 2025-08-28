from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from supabase import create_client, Client
import os

# ----------------------
# تنظیمات
# ----------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------
# مراحل Conversation
# ----------------------
TITLE, CONTENT, ASK_IMAGE, IMAGE = range(4)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! با /add میتونی پست بسازی.")

# شروع افزودن پست
def add_start(update: Update, context: CallbackContext):
    update.message.reply_text("لطفاً عنوان پست رو وارد کن:")
    return TITLE

# دریافت عنوان
def add_title(update: Update, context: CallbackContext):
    context.user_data['title'] = update.message.text
    update.message.reply_text("حالا متن پست رو وارد کن:")
    return CONTENT

# دریافت متن
def add_content(update: Update, context: CallbackContext):
    context.user_data['content'] = update.message.text
    reply_keyboard = [['بله', 'نه']]
    update.message.reply_text(
        "میخوای عکس اضافه کنی؟",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ASK_IMAGE

# پاسخ به اضافه کردن عکس
def ask_image(update: Update, context: CallbackContext):
    answer = update.message.text
    if answer == 'بله':
        update.message.reply_text("لطفاً عکس رو بفرست:", reply_markup=ReplyKeyboardRemove())
        return IMAGE
    else:
        # ذخیره بدون عکس
        supabase.table("posts").insert({
            "title": context.user_data['title'],
            "content": context.user_data['content'],
            "image_url": None
        }).execute()
        update.message.reply_text("✅ پست اضافه شد.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

# دریافت عکس
def add_image(update: Update, context: CallbackContext):
