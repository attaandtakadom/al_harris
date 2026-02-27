import os
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- 1. الإعدادات ---
TOKEN = os.environ.get('TOKEN')
CHANNEL_ID = '-1003569921331' 
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'
APP_URL = "https://attaandtakadom.github.io/atta/"
# الرابط الخاص بك على ريندر
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 2. الدوال الأساسية ---
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
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'check_again':
        await start(update, context)

# --- 3. التشغيل الذكي (Webhook) ---
def main():
    if not TOKEN or not RENDER_URL:
        print("خطأ: تأكد من إضافة TOKEN و RENDER_EXTERNAL_URL في الإعدادات")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    PORT = int(os.environ.get("PORT", 10000))
    
    # هذه الطريقة تجعل ريندر يغلق السيرفر عند عدم الاستخدام ويوفر الساعات
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{RENDER_URL}/{TOKEN}"
    )

if __name__ == '__main__':
    main()
