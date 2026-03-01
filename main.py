import os
import logging
import asyncio
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application

# --- 1. الإعدادات (تأكد من ضبطها في Render Environment) ---
TOKEN = os.environ.get('TOKEN')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- 2. دالة فحص الاشتراك ---
async def check_subscription(user_id):
    try:
        member = await application.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Subscription Check Error: {e}")
        return False

# --- 3. معالجة الرد (المنطق البرمجي) ---
async def process_update_logic(update: Update):
    # الحصول على المستخدم سواء من رسالة أو من ضغطة زر
    user = update.effective_user
    chat_id = update.effective_chat.id
    if not user: return

    # التأكد من الاشتراك
    is_subscribed = await check_subscription(user.id)
    
    if is_subscribed:
        # إذا كان مشتركاً: تظهر له المنظومة
        keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
        text = f"✅ أهلاً بك يا {user.first_name}\nتم التحقق من اشتراكك بنجاح. يمكنك الآن الدخول للمنظومة."
    else:
        # إذا لم يشترك: يظهر له زر الاشتراك
        keyboard = [
            [InlineKeyboardButton("1️⃣ اشترك في القناة أولاً 📢", url=CHANNEL_LINK)],
            [InlineKeyboardButton("2️⃣ اضغط هنا بعد الاشتراك ✅", url=f"https://t.me/{application.bot.username}?start=check")]
        ]
        text = "⚠️ **عذراً، يجب عليك الانضمام للقناة أولاً لتتمكن من استخدام المنظومة!**"

    await application.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# --- 4. الـ Webhook (معدل لاستقبال كل التحديثات) ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        
        # معالجة التحديث سواء كان رسالة نصية أو تفاعل مع زر (Callback)
        if update.message or update.callback_query or update.channel_post:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update_logic(update))
            loop.close()
            
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return "Error", 500

@app.route('/')
def index():
    return "Bot is Live and Ready! 🚀", 200

if __name__ == '__main__':
    # تهيئة أولية للبوت (هام جداً للـ Async)
    init_loop = asyncio.new_event_loop()
    init_loop.run_until_complete(application.initialize())
    init_loop.close()

    # إعادة ضبط الـ Webhook عند التشغيل لضمان صحة الرابط
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}&drop_pending_updates=True")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
