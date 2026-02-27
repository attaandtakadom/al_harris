import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- 1. الإعدادات الأساسية ---
TOKEN = os.environ.get('TOKEN')
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'
APP_URL = "https://attaandtakadom.github.io/atta/"
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 

# إعداد السجلات (Logs) لمراقبة الأداء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. إعداد تطبيق Flask ---
app = Flask(__name__)

# إنشاء تطبيق البوت (بدون تشغيله فوراً)
application = Application.builder().token(TOKEN).build()

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook_handler():
    """استقبال التحديثات من تلجرام وتمريرها للبوت"""
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return "OK", 200

@app.route('/')
def index():
    return "المنظومة تعمل بنظام Webhook بنجاح! 🚀", 200

# --- 3. منطق البوت (Handlers) ---
async def is_user_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subscribed = await is_user_subscribed(context.bot, user.id)
    
    if subscribed:
        keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
        text = f"✅ أهلاً بك يا {user.first_name}\n\nتم التحقق من اشتراكك بنجاح. يمكنك الآن فتح التطبيق:"
    else:
        keyboard = [
            [InlineKeyboardButton("1️⃣ انضم للقناة أولاً 📢", url=CHANNEL_LINK)],
            [InlineKeyboardButton("2️⃣ تأكيد الاشتراك ✅", callback_data='check_again')]
        ]
        text = "⚠️ **عذراً، يجب عليك الانضمام للقناة أولاً!**\n\nيرجى الانضمام ثم العودة والضغط على زر التأكيد."

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'check_again':
        # إعادة تنفيذ دالة start عند الضغط على تأكيد الاشتراك
        user = query.from_user
        subscribed = await is_user_subscribed(context.bot, user.id)
        if subscribed:
            keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
            await query.message.edit_text(f"✅ تم التحقق بنجاح يا {user.first_name}! يمكنك الدخول الآن:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer("❌ لم تشترك في القناة بعد! يرجى الانضمام أولاً.", show_alert=True)

# إضافة المعالجات للتطبيق
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))

# --- 4. تشغيل النظام ---
if __name__ == '__main__':
    if not TOKEN or not RENDER_URL:
        logger.error("خطأ: TOKEN أو RENDER_EXTERNAL_URL مفقود!")
    else:
        # إعداد الـ Webhook برمجياً قبل تشغيل Flask
        async def setup_webhook():
            # حذف الـ Webhook القديم وإسقاط التحديثات المعلقة لحل مشكلة الـ Conflict
            await application.bot.delete_webhook(drop_pending_updates=True)
            # ضبط الـ Webhook الجديد
            webhook_address = f"{RENDER_URL}/{TOKEN}"
            await application.bot.set_webhook(url=webhook_address)
            logger.info(f"Webhook set to: {webhook_address}")

        # تشغيل التهيأة
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(setup_webhook())
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")

        # تشغيل Flask
        PORT = int(os.environ.get("PORT", 10000))
        logger.info(f"Starting Flask app on port {PORT}")
        app.run(host='0.0.0.0', port=PORT)
