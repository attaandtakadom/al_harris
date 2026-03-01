import os
import requests
from flask import Flask, request, jsonify

# جلب التوكن من Environment Variables للأمان
TOKEN = os.environ.get('TOKEN')
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = "-1003569921331"
CHANNEL_LINK = "https://t.me/+PiPTzWzduThiZjBk"

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return f"Server is Live. Webhook status: {'Configured' if TOKEN else 'Missing Token'}", 200

@app.route(f'/{TOKEN}' if TOKEN else '/webhook', methods=['POST'])
def telegram_webhook():
    try:
        # الحصول على البيانات والتأكد من وجودها
        data = request.get_json(force=True, silent=True)
        if not data:
            return "No JSON received", 400

        # استخراج المعرفات (Handle Updates)
        msg_obj = data.get("message") or data.get("callback_query", {}).get("message")
        user_obj = data.get("message", {}).get("from") or data.get("callback_query", {}).get("from")

        if user_obj and msg_obj:
            chat_id = msg_obj["chat"]["id"]
            user_id = user_obj["id"]

            # التحقق من الاشتراك (Sub Check) مع Exception
            is_member = False
            try:
                check_url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
                res = requests.post(check_url, json={"chat_id": CHANNEL_ID, "user_id": user_id}, timeout=8).json()
                if res.get("ok") and res["result"]["status"] in ['member', 'administrator', 'creator']:
                    is_member = True
            except Exception as e:
                print(f"Sub-check Error: {e}")

            # بناء الرد
            if is_member:
                text = "✅ تم التحقق بنجاح! يمكنك الآن الدخول للمنظومة."
                kb = {"inline_keyboard": [[{"text": "دخول المنظومة 📱", "web_app": {"url": APP_URL}}]]}
            else:
                text = "⚠️ يجب عليك الاشتراك في القناة أولاً لاستخدام البوت."
                kb = {"inline_keyboard": [
                    [{"text": "1️⃣ انضم للقناة", "url": CHANNEL_LINK}],
                    [{"text": "2️⃣ اضغط للتفعيل ✅", "url": f"https://t.me/takadom2026bot?start=check"}]
                ]}

            # إرسال الرسالة
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": text, "reply_markup": kb}, timeout=8)

    except Exception as e:
        print(f"Global Error: {e}")
    
    # الرد بـ 200 دائماً لمنع التبريم
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
