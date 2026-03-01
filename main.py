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
CHANNEL_USERNAME = "your_channel_username"  # استخدم username بدلاً من ID
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# --- 2. دوال المساعدة ---
async def check_subscription(user_id):
    try:
        # استخدم username إن أمكن
        member = await application.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطأ في فحص الاشتراك: {e}")
        return False

# --- 3. معالج أمر /start ---
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

# --- 4. معالج الضغط على الأزرار ---
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

# --- 5. تسجيل المعالجات ---
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CallbackQueryHandler(button_handler))

# --- 6. Webhook ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        
        # معالجة التحديث بشكل غير متزامن
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return "OK", 200

@app.route('/')
def index():
    return "Bot is running!", 200

if __name__ == '__main__':
    # تعيين webhook
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
