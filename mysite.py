from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

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
# Dispatcher برای مدیریت دستورات
# ----------------------
dispatcher = Dispatcher(bot, None, workers=0)

# --- دستورات ربات ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! با /add میتونی پست بسازی.")

def add(update: Update, context: CallbackContext):
    try:
        text = " ".join(context.args)
        title, content = text.split("|")
        supabase.table("posts").insert({
            "title": title.strip(),
            "content": content.strip()
        }).execute()
        update.message.reply_text("✅ پست اضافه شد.")
    except:
        update.message.reply_text("❌ فرمت درست نیست:\n/add عنوان | متن پست")

def delete(update: Update, context: CallbackContext):
    try:
        post_id = int(context.args[0])
        supabase.table("posts").delete().eq("id", post_id).execute()
        update.message.reply_text("🗑 پست حذف شد.")
    except:
        update.message.reply_text("❌ فرمت درست نیست:\n/delete 1")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("add", add))
dispatcher.add_handler(CommandHandler("delete", delete))

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
