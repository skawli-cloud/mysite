from flask import Flask, request, jsonify
from flask_cors import CORS  # اضافه شد
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
CORS(app)  # فعال کردن CORS برای همه منابع

# ----------------------
# مراحل Conversation
# ----------------------
TITLE, CONTENT, ASK_IMAGE, IMAGE = range(4)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! با /add میتونی پست بسازی.")

def add_start(update: Update, context: CallbackContext):
    update.message.reply_text("لطفاً عنوان پست رو وارد کن:")
    return TITLE

def add_title(update: Update, context: CallbackContext):
    context.user_data['title'] = update.message.text
    update.message.reply_text("حالا متن پست رو وارد کن:")
    return CONTENT

def add_content(update: Update, context: CallbackContext):
    context.user_data['content'] = update.message.text
    reply_keyboard = [['بله', 'نه']]
    update.message.reply_text(
        "میخوای عکس اضافه کنی؟",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ASK_IMAGE

def ask_image(update: Update, context: CallbackContext):
    answer = update.message.text
    if answer == 'بله':
        update.message.reply_text("لطفاً عکس رو بفرست:", reply_markup=ReplyKeyboardRemove())
        return IMAGE
    else:
        supabase.table("posts").insert({
            "title": context.user_data['title'],
            "content": context.user_data['content'],
            "image_url": None
        }).execute()
        update.message.reply_text("✅ پست اضافه شد.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

def add_image(update: Update, context: CallbackContext):
    photo_file = update.message.photo[-1].get_file()
    image_url = photo_file.file_path  # بهتره بعداً روی Supabase Storage آپلود بشه
    supabase.table("posts").insert({
        "title": context.user_data['title'],
        "content": context.user_data['content'],
        "image_url": image_url
    }).execute()
    update.message.reply_text("✅ پست همراه با عکس اضافه شد!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ----------------------
# Dispatcher ربات
# ----------------------
dispatcher = Dispatcher(bot, None, workers=0)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('add', add_start)],
    states={
        TITLE: [MessageHandler(Filters.text & ~Filters.command, add_title)],
        CONTENT: [MessageHandler(Filters.text & ~Filters.command, add_content)],
        ASK_IMAGE: [MessageHandler(Filters.regex('^(بله|نه)$'), ask_image)],
        IMAGE: [MessageHandler(Filters.photo, add_image)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(conv_handler)

# ----------------------
# Webhook endpoint
# ----------------------
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# ----------------------
# API ساده برای سایت
# ----------------------
@app.route("/posts", methods=["GET"])
def get_posts():
    data = supabase.table("posts").select("*").execute()
    return jsonify(data.data)

@app.route("/posts", methods=["POST"])
def add_post():
    req = request.json
    data = supabase.table("posts").insert({
        "title": req["title"],
        "content": req["content"],
        "image_url": req.get("image_url", None)
    }).execute()
    return jsonify(data.data)

@app.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    data = supabase.table("posts").delete().eq("id", post_id).execute()
    return jsonify(data.data)

# ----------------------
# اجرای اصلی
# ----------------------
if __name__ == "__main__":
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=5000)
