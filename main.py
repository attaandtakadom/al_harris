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

# مخزن مؤقت لمنع تكرار الرسائل (Idempotency)
processed_updates = set()

# --- 2. دالة فحص الاشتراك المحسنة ---
async def check_subscription(user_id):
    try:
        # إضافة تأخير بسيط لضمان تحديث قاعدة بيانات تلجرام
        member = await application.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # الحالات التي يعتبر فيها المستخدم مشتركاً
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطأ في فحص الاشتراك: {e}")
        return False

# --- 3. المنطق البرمجي ---
async def process_update_logic(update: Update):
    user = update.effective_user
    if not user: return

    # فحص الاشتراك
    is_subscribed = await check_subscription(user.id)
    
    if is_subscribed:
        keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
        text = f"✅ أهلاً بك يا {user.first_name}\nتم التأكد من انضمامك للقناة بنجاح!"
    else:
        keyboard = [
            [InlineKeyboardButton("1️⃣ اشترك في القناة أولاً 📢", url=CHANNEL_LINK)],
            [InlineKeyboardButton("2️⃣ اضغط هنا للتفعيل ✅", url=f"https://t.me/takadom2026bot?start=check")]
        ]
        text = "⚠️ **عذراً! لم نجد اسمك في القناة.**\n\nيرجى الاشتراك أولاً ثم العودة والضغط على زر التفعيل."

    try:
        await application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")

# --- 4. الـ Webhook مع مانع التكرار ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update_id = update_json.get('update_id')

        # منع تكرار المعالجة لنفس الرسالة
        if update_id in processed_updates:
            return "OK", 200
        
        processed_updates.add(update_id)
        # تنظيف المخزن إذا كبر حجمه
        if len(processed_updates) > 1000:
            processed_updates.clear()

        update = Update.de_json(update_json, application.bot)
        
        # إنشاء Loop للمعالجة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_update_logic(update))
        loop.close()
            
        return "OK", 200 # الرد فوراً بـ OK لتلجرام لمنع إعادة الإرسال
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return "OK", 200 # نرسل OK حتى في الخطأ لمنع التكرار المزعج

@app.route('/')
def index():
    return "Bot status: stable", 200

if __name__ == '__main__':
    # إعادة ضبط الـ Webhook عند التشغيل
    webhook_target = f"{RENDER_URL}/{TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_target}&drop_pending_updates=True")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
