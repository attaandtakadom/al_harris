import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- 1. خادم الاستيقاظ (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "المنظومة التعليمية تنبض بنجاح! 🚀"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. الإعدادات الأساسية ---
TOKEN = os.environ.get('TOKEN')
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'
APP_URL = "https://attaandtakadom.github.io/atta/"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 3. دالة فحص الاشتراك ---
async def is_user_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        allowed_statuses = ['member', 'administrator', 'creator']
        return member.status in allowed_statuses
    except Exception as e:
        logging.error(f"خطأ في فحص العضوية: {e}")
        return False

# --- 4. معالجة أمر البداية /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    subscribed = await is_user_subscribed(context.bot, user_id)
    
    if subscribed:
        keyboard = [[InlineKeyboardButton("دخول المنظومة 📱", web_app=WebAppInfo(url=APP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"✅ أهلاً بك يا {user.first_name}\n\nلقد تم التحقق من اشتراكك بنجاح. يمكنك الآن فتح التطبيق التعليمي:"
    else:
        keyboard = [
            [InlineKeyboardButton("1️⃣ انضم للقناة أولاً 📢", url=CHANNEL_LINK)],
            [InlineKeyboardButton("2️⃣ تأكيد الاشتراك ✅", callback_data='check_again')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "⚠️ **عذراً، يجب عليك الانضمام للقناة أولاً!**\n\nيرجى الانضمام ثم العودة والضغط على زر التأكيد."

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# --- 5. معالج الأزرار ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'check_again':
        await start(update, context)

# --- 6. تشغيل البوت ---
def main():
    if not TOKEN:
        return
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

if __name__ == '__main__':
    main()
