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
# إنشاء التطبيق مع ضبط ميزات السرعة
application = Application.builder().token(TOKEN).build()

# --- 2. المنطق البرمجي (سرعة قصوى) ---
async def process_update(update: Update):
    try:
        user = update.effective_user
        if not user: return

        # فحص سريع للاشتراك
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
        logger.error(f"Error: {e}")

# --- 3. الـ Webhook المستقر بنسبة 100% ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update_json = request.get_json(force=True)
    update = Update.de_json(update_json, application.bot)
    
    # استخدام Loop موحد بدلاً من إنشاء وإغلاق Loop جديد
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # تشغيل المعالجة في الخلفية لضمان رد الـ OK فوراً لتلجرام
    loop.create_task(process_update(update))
    
    return "OK", 200

@app.route('/')
def index():
    return "Bot is Active and Fast! 🚀", 200

if __name__ == '__main__':
    # تهيئة البوت
    init_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(init_loop)
    init_loop.run_until_complete(application.initialize())
    
    # ضبط الـ Webhook
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}&drop_pending_updates=True")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
