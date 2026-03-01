import os
import logging
import requests
from flask import Flask, request, jsonify

# إعداد السجلات (Logs) لمراقبة الأخطاء في Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب البيانات من البيئة (Environment Variables) للأمان
TOKEN = os.environ.get('TOKEN')
APP_URL = "https://attaandtakadom.github.io/atta/"
CHANNEL_ID = "-1003569921331"
CHANNEL_LINK = "https://t.me/+PiPTzWzduThiZjBk"

app = Flask(__name__)

def check_sub(uid):
    """التحقق من الاشتراك مع معالجة الاستثناءات"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
        response = requests.post(url, json={"chat_id": CHANNEL_ID, "user_id": uid}, timeout=10)
        result = response.json()
        return result.get("ok") and result["result"]["status"] in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

@app.route(f'/{TOKEN}' if TOKEN else '/webhook', methods=['POST'])
def webhook():
    """المسار الرئيسي لاستقبال تحديثات تلجرام مع Exceptions شاملة"""
    try:
        data = request.get_json()
        if not data:
            return "No data", 400
        
        # استخراج معلومات الرسالة أو ضغطة الزر
        update_obj = data.get("message") or data.get("callback_query", {}).get("message")
        user_obj = (data.get("message", {}).get("from") or 
                    data.get("callback_query", {}).get("from"))

        if user_obj and update_obj:
            uid = user_obj["id"]
            chat_id = update_obj["chat"]["id"]
            
            # منطق التحقق والرد
            if check_sub(uid):
                txt = "✅ تم التحقق من اشتراكك بنجاح! يمكنك الآن الدخول."
                kb = {"inline_keyboard": [[{"text": "دخول المنظومة 📱", "web_app": {"url": APP_URL}}]]}
            else:
                txt = "⚠️ عفواً، يجب عليك الانضمام للقناة أولاً."
                kb = {"inline_keyboard": [
                    [{"text": "1️⃣ انضم للقناة من هنا", "url": CHANNEL_LINK}],
                    [{"text": "2️⃣ اضغط للتفعيل بعد الانضمام ✅", "callback_data": "check_now"}]
                ]}

            # إرسال الرد
            send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(send_url, json={
                "chat_id": chat_id, 
                "text": txt, 
                "reply_markup": kb, 
                "parse_mode": "Markdown"
            }, timeout=10)

    except Exception as e:
        logger.error(f"General Webhook Error: {e}")
    
    # نرد دائماً بـ 200 لتجنب "التبريم" وتراكم الرسائل في تلجرام
    return "OK", 200

@app.route('/')
def health_check():
    """مسار لفحص حالة السيرفر من المتصفح"""
    status = "Active" if TOKEN else "Token Missing"
    return jsonify({"status": status, "message": "Server is running smoothly"}), 200

if __name__ == "__main__":
    # تشغيل السيرفر
    app.run(host='0.0.0.0', port=10000)
