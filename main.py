import os
import logging
import requests
from flask import Flask, request

# --- 1. الإعدادات ---
TOKEN = os.environ.get('TOKEN')
RENDER_URL = "https://al-harris.onrender.com"
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = '-1003569921331'
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- 2. وظائف التفاعل عبر API تلجرام المباشر ---

def send_telegram_request(method, data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Telegram API Error ({method}): {e}")
        return None

def check_subscription(user_id):
    data = {"chat_id": CHANNEL_ID, "user_id": user_id}
    res = send_telegram_request("getChatMember", data)
    if res and res.get("ok"):
        status = res["result"]["status"]
        return status in ['member', 'administrator', 'creator']
    return False

def handle_logic(update):
    if "message" in update:
        user = update["message"]["from"]
        chat_id = update["message"]["chat"]["id"]
    elif "callback_query" in update:
        user = update["callback_query"]["from"]
        chat_id = update["callback_query"]["message"]["chat"]["id"]
    else:
        return

    user_id = user["id"]
    first_name = user.get("first_name", "أهلاً بك")

    if check_subscription(user_id):
        text = f"✅ أهلاً بك يا {first_name}\nتم التحقق من اشتراكك بنجاح. يمكنك الدخول للمنظومة الآن:"
        keyboard = {"inline_keyboard": [[{"text": "دخول المنظومة 📱", "web_app": {"url": APP_URL}}]]}
    else:
        text = "⚠️ **عذراً! يجب عليك الانضمام للقناة أولاً لتتمكن من استخدام المنظومة!**"
        keyboard = {"inline_keyboard": [
            [{"text": "1️⃣ اشترك في القناة أولاً 📢", "url": CHANNEL_LINK}],
            [{"text": "2️⃣ اضغط هنا للتفعيل ✅", "url": f"https://t.me/takadom2026bot?start=check"}]
        ]}

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard,
        "parse_mode": "Markdown"
    }
    send_telegram_request("sendMessage", payload)

# --- 3. الـ Webhook المستقر ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json(force=True)
    # المعالجة فوراً دون الحاجة لـ Loop أو Threads معقدة
    handle_logic(update)
    return "OK", 200

@app.route('/')
def index():
    return "Bot is stable and running! 🚀", 200

if __name__ == '__main__':
    # ضبط الـ Webhook عند التشغيل
    webhook_target = f"{RENDER_URL}/{TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_target}&drop_pending_updates=True")
    
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
