import os
import logging
import asyncio
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. الإعدادات ---
TOKEN = os.environ.get('TOKEN')
RENDER_URL = "https://al-harris.onrender.com" 
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = '-1003569921331'  # يمكنك استخدام ID القناة
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'

logging.basicConfig(format='%(asime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- 2. تهيئة التطبيق (مصححة) ---
application = Application.builder().token(TOKEN).build()

# --- 3. دوال المساعدة ---
async def check_subscription(user_id):
    try:
        # تهيئة التطبيق إذا لم يكن مهيأً
        if not application._initialized:
            await application.initialize()
            
        member = await application.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطأ في فحص الاشتراك: {e}")
        return False

# --- 4. معالج أمر /start ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # فحص الاشتراك
    is_subscribed = await check_subscription(user.id)
    
    if is_subscribed:
        keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
        text = f"✅ أهلاً بك يا {user.first_name}\nتم التأكد من انضمامك للقناة بنجاح!"
    else:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")]
        ]
        text = "⚠️ **عذراً! يجب الاشتراك في القناة أولاً**\n\nاشترك ثم اضغط على زر التحقق."

    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# --- 5. معالج الضغط على الأزرار ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_subscription":
        user = update.effective_user
        is_subscribed = await check_subscription(user.id)
        
        if is_subscribed:
            keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
            await query.edit_message_text(
                text=f"✅ تم التحقق بنجاح! أهلاً بك يا {user.first_name}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                text="❌ لم يتم الاشتراك بعد. يرجى الاشتراك في القناة أولاً.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 اشترك الآن", url=CHANNEL_LINK)
                ]])
            )

# --- 6. تسجيل المعالجات ---
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CallbackQueryHandler(button_handler))

# --- 7. Webhook معالج ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        
        # معالجة التحديث بشكل غير متزامن مع تهيئة التطبيق
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # تهيئة التطبيق قبل المعالجة
        if not application._initialized:
            loop.run_until_complete(application.initialize())
        
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return "OK", 200

@app.route('/')
def index():
    return "Bot is running!", 200

@app.route('/setwebhook')
def set_webhook():
    """Endpoint يدوي لتعيين webhook"""
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    return response.json()

if __name__ == '__main__':
    # تعيين webhook
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    logger.info(f"Webhook set response: {response.json()}")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
