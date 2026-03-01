import os
import requests
from flask import Flask, request

TOKEN = os.environ.get('TOKEN')
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = '-1003569921331'
CHANNEL_LINK = 'https://t.me/+PiPTzWzduThiZjBk'
RENDER_URL = "https://al-harris.onrender.com"

app = Flask(__name__)

def check_sub(uid):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
        r = requests.post(url, json={"chat_id": CHANNEL_ID, "user_id": uid}, timeout=5).json()
        return r.get("ok") and r["result"]["status"] in ['member', 'administrator', 'creator']
    except: return False

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    # استخراج البيانات سواء كانت رسالة عادية أو ضغطة زر
    msg = data.get("message") or data.get("callback_query", {}).get("message")
    user = data.get("message", {}).get("from") or data.get("callback_query", {}).get("from")
    
    if user and msg:
        uid = user["id"]
        chat_id = msg["chat"]["id"]
        first_name = user.get("first_name", "")

        if check_sub(uid):
            txt = f"✅ أهلاً {first_name}\nتم التحقق من اشتراكك بنجاح!"
            kb = {"inline_keyboard": [[{"text": "دخول المنظومة 📱", "web_app": {"url": APP_URL}}]]}
        else:
            txt = "⚠️ يجب الاشتراك في القناة أولاً لاستخدام البوت."
            kb = {"inline_keyboard": [
                [{"text": "1️⃣ اشترك هنا", "url": CHANNEL_LINK}],
                [{"text": "2️⃣ اضغط للتفعيل ✅", "url": f"https://t.me/takadom2026bot?start=check"}]
            ]}
        
        # إرسال الرد فوراً
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": chat_id, "text": txt, "reply_markup": kb, "parse_mode": "Markdown"})
    
    return "OK", 200

@app.route('/')
def hi(): return "Bot is Fast Now!", 200

if __name__ == '__main__':
    # أهم خطوة: تنظيف الرسائل القديمة (drop_pending_updates) وتفعيل الرابط الجديد
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={RENDER_URL}/{TOKEN}&drop_pending_updates=True")
    app.run(host='0.0.0.0', port=10000)
