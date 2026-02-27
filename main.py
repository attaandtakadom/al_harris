import os
import logging
import asyncio
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application

# --- 1. الإعدادات ---
TOKEN = os.environ.get('TOKEN')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 
APP_URL = "https://attaandtakadom.github.io/atta/"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# إنشاء البوت
application = Application.builder().token(TOKEN).build()

# --- 2. دالة المعالجة المباشرة ---
async def process_start(update: Update):
    """منطق الرد على المستخدم"""
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await application.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ أهلاً بك يا {user.first_name}\nالمنظومة جاهزة للعمل:",
        reply_markup=reply_markup
    )

# --- 3. الـ Webhook المباشر ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """استلام الطلب ومعالجته بأسلوب مباشر لتجنب الـ Exception"""
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        
        if update.message and update.message.text == "/start":
            # تشغيل المعالجة في Event Loop منفصل لضمان الاستقرار
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_start(update))
            loop.close()
            
        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing: {e}")
        return "Error", 500

@app.route('/')
def index():
    return "Bot is active!", 200

# --- 4. تشغيل وضبط الـ Webhook ---
if __name__ == '__main__':
    # مسح أي تضارب قديم وضبط الجديد
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True")
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={RENDER_URL}/{TOKEN}")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
