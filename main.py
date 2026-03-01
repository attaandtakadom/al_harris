import os
import logging
import asyncio
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application

# --- 1. الإعدادات ---
TOKEN = os.environ.get('TOKEN')
RENDER_URL = "https://al-harris.onrender.com" 
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- 2. معالجة الرد (بشكل سريع) ---
async def handle_logic(update: Update):
    try:
        user = update.effective_user
        if not user: return

        # فحص الاشتراك
        member = await application.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        is_subscribed = member.status in ['member', 'administrator', 'creator']
        
        if is_subscribed:
            keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
            text = f"✅ أهلاً بك يا {user.first_name}\nتم التحقق من اشتراكك بنجاح."
        else:
            keyboard = [
                [InlineKeyboardButton("1️⃣ اشترك في القناة أولاً 📢", url=CHANNEL_LINK)],
                [InlineKeyboardButton("2️⃣ اضغط هنا للتفعيل ✅", url=f"https://t.me/takadom2026bot?start=check")]
            ]
            text = "⚠️ **عذراً! يجب عليك الانضمام للقناة أولاً.**"

        await application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Logic Error: {e}")

# --- 3. الـ Webhook السريع جداً ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update_json = request.get_json(force=True)
    update = Update.de_json(update_json, application.bot)
    
    # تشغيل المعالجة في "الخلفية" دون تعطيل الرد على تلجرام
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.create_task(handle_logic(update))
    
    return "OK", 200 # الرد فوراً لإيقاف علامة التحميل في تلجرام

@app.route('/')
def index():
    return "Status: Active 🚀", 200

if __name__ == '__main__':
    # تهيئة أولية سريعة
    init_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(init_loop)
    init_loop.run_until_complete(application.initialize())
    
    # ضبط الـ Webhook
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={RENDER_URL}/{TOKEN}&drop_pending_updates=True")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
