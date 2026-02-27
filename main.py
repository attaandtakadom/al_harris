import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- 1. الإعدادات ---
TOKEN = os.environ.get('TOKEN')
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'
APP_URL = "https://attaandtakadom.github.io/atta/"
# رابط Render الخاص بك (مثال: https://al-harris.onrender.com)
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. إنشاء تطبيق Flask لاستقبال الـ Webhook ---
app = Flask(__name__)

# إنشاء تطبيق البوت
application = Application.builder().token(TOKEN).build()

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook_handler():
    """استقبال التحديثات من تلجرام وتمريرها للبوت"""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
    return "OK", 200

@app.route('/')
def index():
    return "المنظومة تعمل بنظام Webhook 🚀"

# --- 3. الدوال الأساسية للبوت ---
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
        text = f"✅ أهلاً بك يا {user.first_name}\n\nتم التحقق من اشتراكك بنجاح."
    else:
        keyboard = [
            [InlineKeyboardButton("1️⃣ انضم للقناة أولاً 📢", url=CHANNEL_LINK)],
            [InlineKeyboardButton("2️⃣ تأكيد الاشتراك ✅", callback_data='check_again')]
        ]
        text = "⚠️ **عذراً، يجب عليك الانضمام للقناة أولاً!**"

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'check_again':
        user = query.from_user
        subscribed = await is_user_subscribed(context.bot, user.id)
        if subscribed:
            keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
            await query.message.edit_text(f"✅ تم التحقق بنجاح يا {user.first_name}!", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer("❌ لم تشترك في القناة بعد!", show_alert=True)

# --- 4. إعداد الـ Handlers وتجهيز البوت ---
# سنستخدم هذا الجزء لتهيئة البوت قبل تشغيل Flask
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))

# --- 5. تشغيل السيرفر ---
if __name__ == '__main__':
    # إخبار تلجرام بالرابط الجديد
    import asyncio
    async def set_webhook():
        await application.bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    
    # تشغيل Flask على المنفذ المطلوب
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
