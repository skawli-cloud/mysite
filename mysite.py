from flask import Flask, request, jsonify
from supabase import create_client, Client
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os

# --- تنظیمات ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

# --- API ---
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

# --- ربات تلگرام ---
def start(update, context):
    update.message.reply_text("سلام! می‌تونی با دستور /add عنوان | متن پست بسازی.")

def add(update, context):
    try:
        text = " ".join(context.args)
        title, content = text.split("|")
        supabase.table("posts").insert({
            "title": title.strip(),
            "content": content.strip()
        }).execute()
        update.message.reply_text("✅ پست اضافه شد.")
    except:
        update.message.reply_text("❌ فرمت درست نیست. مثال:\n/add عنوان | متن پست")

def delete(update, context):
    try:
        post_id = int(context.args[0])
        supabase.table("posts").delete().eq("id", post_id).execute()
        update.message.reply_text("🗑 پست حذف شد.")
    except:
        update.message.reply_text("❌ فرمت درست نیست. مثال:\n/delete 1")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("delete", delete))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # اجرای همزمان Flask و ربات
    import threading
    threading.Thread(target=main).start()
    app.run(host="0.0.0.0", port=5000)
