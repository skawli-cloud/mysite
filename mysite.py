from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
from telegram import Update, Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# ----------------------
# تنظیمات
# ----------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://your-app.onrender.com/telegram

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

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
