import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. الإعدادات واستخراج المتغيرات ---
TOKEN = os.environ.get('TOKEN')
# تأكد أن هذا الرابط هو رابط تطبيقك على ريندر بدون / في النهاية
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'

# إعداد السجلات (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. إعداد Flask و Telegram Application ---
app = Flask(__name__)
# إنشاء تطبيق البوت
application = Application.builder().token(TOKEN).build()

# --- 3. منطق البوت (Handlers) ---
async def is_user_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subscribed = await is_user_subscribed(context.bot, user.id)
    
    if subscribed:
        keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
        text = f"✅ أهلاً بك يا {user.first_name}\n\nتم التحقق من اشتراكك بنجاح. يمكنك الآن الدخول:"
    else:
        keyboard = [
            [InlineKeyboardButton("1️⃣ انضم للقناة أولاً 📢", url=CHANNEL_LINK)],
            [InlineKeyboardButton("2️⃣ تأكيد الاشتراك ✅", callback_data='check_again')]
        ]
        text = "⚠️ **عذراً، يجب عليك الانضمام للقناة أولاً!**"

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# إضافة الأوامر للتطبيق
application.add_handler(CommandHandler("start", start))

# --- 4. إعدادات الـ Webhook واستقبال الطلبات ---
@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    """هذه الدالة تستقبل الرسائل من تلجرام وتمررها للبوت"""
    if request.method == "POST":
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            # استخدام initialize لضمان أن البوت جاهز لمعالجة الطلب
            async with application:
                await application.process_update(update)
            return "OK", 200
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return "Error", 500
    return "Forbidden", 403

@app.route('/')
def home():
    return "Bot is active and running via Webhook! 🚀", 200

# --- 5. تشغيل السيرفر وضبط الـ Webhook يدوياً ---
def run_bot():
    # محاولة ضبط الـ Webhook عند بدء التشغيل باستخدام طلب خارجي بسيط لضمان الفاعلية
    import requests
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}&drop_pending_updates=True")
    logger.info(f"Webhook status: {response.json()}")

    PORT = int(os.environ.get("PORT", 10000))
    # تشغيل Flask
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    run_bot()
