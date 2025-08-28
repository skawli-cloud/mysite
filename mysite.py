from flask import Flask, request, jsonify
from flask_cors import CORS
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
CORS(app)  # فعال کردن CORS

# ----------------------
# مراحل Conversation
# ----------------------
ADD_TITLE, ADD_CONTENT, ADD_ASK_IMAGE, ADD_IMAGE = range(4)
EDIT_SELECT, EDIT_FIELD, EDIT_CONTENT, EDIT_IMAGE = range(4, 8)
DELETE_SELECT = 8

# ----------------------
# دستور /start
# ----------------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! میتونی /add پست جدید بسازی، /edit پست رو ویرایش کنی و /delete پست رو حذف کنی.")

# ----------------------
# دستور /add
# ----------------------
def add_start(update: Update, context: CallbackContext):
    update.message.reply_text("لطفاً عنوان پست رو وارد کن:")
    return ADD_TITLE

def add_title(update: Update, context: CallbackContext):
    context.user_data['title'] = update.message.text
    update.message.reply_text("حالا متن پست رو وارد کن:")
    return ADD_CONTENT

def add_content(update: Update, context: CallbackContext):
    context.user_data['content'] = update.message.text
    reply_keyboard = [['بله', 'نه']]
    update.message.reply_text(
        "میخوای عکس اضافه کنی؟",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ADD_ASK_IMAGE

def add_ask_image(update: Update, context: CallbackContext):
    answer = update.message.text
    if answer == 'بله':
        update.message.reply_text("لطفاً عکس رو بفرست:", reply_markup=ReplyKeyboardRemove())
        return ADD_IMAGE
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
    image_url = photo_file.file_path  # می‌تونی این رو روی Supabase Storage آپلود کنی
    supabase.table("posts").insert({
        "title": context.user_data['title'],
        "content": context.user_data['content'],
        "image_url": image_url
    }).execute()
    update.message.reply_text("✅ پست همراه با عکس اضافه شد!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ----------------------
# دستور /edit
# ----------------------
def edit_start(update: Update, context: CallbackContext):
    data = supabase.table("posts").select("*").execute().data
    if not data:
        update.message.reply_text("هیچ پستی وجود ندارد.")
        return ConversationHandler.END
    context.user_data['posts'] = {str(p['id']): p for p in data}
    message = "کد پست برای ویرایش را انتخاب کن:\n"
    for p in data:
        message += f"{p['id']}: {p['title']}\n"
    update.message.reply_text(message)
    return EDIT_SELECT

def edit_select(update: Update, context: CallbackContext):
    post_id = update.message.text
    if post_id not in context.user_data['posts']:
        update.message.reply_text("کد پست نامعتبر است. دوباره امتحان کن.")
        return EDIT_SELECT
    context.user_data['edit_id'] = post_id
    reply_keyboard = [['عنوان', 'متن', 'عکس']]
    update.message.reply_text(
        "کدام بخش را ویرایش می‌کنی؟",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return EDIT_FIELD

def edit_field(update: Update, context: CallbackContext):
    field = update.message.text
    context.user_data['edit_field'] = field
    if field in ['عنوان', 'متن']:
        update.message.reply_text(f"لطفاً {field} جدید را وارد کن:", reply_markup=ReplyKeyboardRemove())
        return EDIT_CONTENT
    else:  # عکس
        update.message.reply_text("لطفاً عکس جدید را ارسال کن:", reply_markup=ReplyKeyboardRemove())
        return EDIT_IMAGE

def edit_content(update: Update, context: CallbackContext):
    post_id = context.user_data['edit_id']
    field = context.user_data['edit_field']
    value = update.message.text
    col = 'title' if field=='عنوان' else 'content'
    supabase.table("posts").update({col: value}).eq("id", int(post_id)).execute()
    update.message.reply_text("✅ پست ویرایش شد.")
    return ConversationHandler.END

def edit_image(update: Update, context: CallbackContext):
    post_id = context.user_data['edit_id']
    photo_file = update.message.photo[-1].get_file()
    image_url = photo_file.file_path
    supabase.table("posts").update({"image_url": image_url}).eq("id", int(post_id)).execute()
    update.message.reply_text("✅ عکس پست ویرایش شد.")
    return ConversationHandler.END

# ----------------------
# دستور /delete
# ----------------------
def delete_start(update: Update, context: CallbackContext):
    data = supabase.table("posts").select("*").execute().data
    if not data:
        update.message.reply_text("هیچ پستی وجود ندارد.")
        return ConversationHandler.END
    context.user_data['posts'] = {str(p['id']): p for p in data}
    message = "کد پست برای حذف را انتخاب کن:\n"
    for p in data:
        message += f"{p['id']}: {p['title']}\n"
    update.message.reply_text(message)
    return DELETE_SELECT

def delete_select(update: Update, context: CallbackContext):
    post_id = update.message.text
    if post_id not in context.user_data['posts']:
        update.message.reply_text("کد پست نامعتبر است. دوباره امتحان کن.")
        return DELETE_SELECT
    supabase.table("posts").delete().eq("id", int(post_id)).execute()
    update.message.reply_text("✅ پست حذف شد.")
    return ConversationHandler.END

# ----------------------
# cancel
# ----------------------
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ----------------------
# Dispatcher ربات
# ----------------------
dispatcher = Dispatcher(bot, None, workers=0)

# ConversationHandler برای add
conv_add = ConversationHandler(
    entry_points=[CommandHandler('add', add_start)],
    states={
        ADD_TITLE: [MessageHandler(Filters.text & ~Filters.command, add_title)],
        ADD_CONTENT: [MessageHandler(Filters.text & ~Filters.command, add_content)],
        ADD_ASK_IMAGE: [MessageHandler(Filters.regex('^(بله|نه)$'), add_ask_image)],
        ADD_IMAGE: [MessageHandler(Filters.photo, add_image)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# ConversationHandler برای edit
conv_edit = ConversationHandler(
    entry_points=[CommandHandler('edit', edit_start)],
    states={
        EDIT_SELECT: [MessageHandler(Filters.text & ~Filters.command, edit_select)],
        EDIT_FIELD: [MessageHandler(Filters.regex('^(عنوان|متن|عکس)$'), edit_field)],
        EDIT_CONTENT: [MessageHandler(Filters.text & ~Filters.command, edit_content)],
        EDIT_IMAGE: [MessageHandler(Filters.photo, edit_image)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# ConversationHandler برای delete
conv_delete = ConversationHandler(
    entry_points=[CommandHandler('delete', delete_start)],
    states={
        DELETE_SELECT: [MessageHandler(Filters.text & ~Filters.command, delete_select)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(conv_add)
dispatcher.add_handler(conv_edit)
dispatcher.add_handler(conv_delete)

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
