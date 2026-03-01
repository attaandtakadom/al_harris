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
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# إنشاء التطبيق لمرة واحدة
application = Application.builder().token(TOKEN).build()

# --- 2. دالة المعالجة الأساسية ---
async def handle_update(update: Update):
    user = update.effective_user
    if not user: return

    try:
        # فحص الاشتراك مباشرة من البوت
        member = await application.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        is_subscribed = member.status in ['member', 'administrator', 'creator']
        
        if is_subscribed:
            keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
            text = f"✅ أهلاً بك يا {user.first_name}\nتم التحقق من اشتراكك بنجاح."
        else:
            keyboard = [
                [InlineKeyboardButton("1️⃣ اشترك في القناة أولاً 📢", url=CHANNEL_LINK)],
                [InlineKeyboardButton("2️⃣ اضغط هنا بعد الاشتراك ✅", url=f"https://t.me/{application.bot.username}?start=check")]
            ]
            text = "⚠️ **عذراً، يجب عليك الانضمام للقناة أولاً لتتمكن من استخدام المنظومة!**"

        await application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in handle_update: {e}")

# --- 3. الـ Webhook المستقر ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        
        # الحل السحري: إنشاء Loop جديد كلياً لكل طلب ومعالجته حتى النهاية
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(handle_update(update))
        new_loop.close()
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook Exception: {e}")
        return "Error", 500

@app.route('/')
def index():
    return "Bot is stable and running! 🚀", 200

if __name__ == '__main__':
    # تهيئة البوت وضبط الـ Webhook
    webhook_path = f"{RENDER_URL}/{TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_path}&drop_pending_updates=True")
    
    # تهيئة أولية للتطبيق
    temp_loop = asyncio.new_event_loop()
    temp_loop.run_until_complete(application.initialize())
    temp_loop.close()
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
