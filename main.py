import logging
from flask import Flask, request, jsonify
import sqlite3
import requests
import os
from pharmacies import get_all_pharmacies, get_open_pharmacies

app = Flask(__name__)
DB_NAME = os.path.join(os.getcwd(), "services.db")

# إعداد التسجيل
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

ULTRAMSG_INSTANCE_ID = os.environ.get("ULTRAMSG_INSTANCE_ID", "instance130542")
ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN", "pr2bhaor2vevcrts")

# دالة الإرسال عبر واتساب
def send_whatsapp_message(phone, message):
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": phone,
        "body": message
    }
    try:
        response = requests.post(url, data=payload)
        logging.info(f"تم إرسال الرد إلى {phone}: {message}")
        return response.json()
    except Exception as e:
        logging.error(f"خطأ أثناء إرسال الرسالة: {e}")
        return None

# نقطة الاستقبال من الواتساب
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message", "").strip()
    sender = data.get("sender")

    if not message or not sender:
        return jsonify({"status": "ignored", "reason": "missing message or sender"})

    # الردود الذكية حسب الرسالة
    message_lower = message.lower()

    if message_lower in ["جميع الصيدليات", "كل الصيدليات"]:
        reply = get_all_pharmacies()
    elif message_lower in ["الصيدليات المفتوحة", "صيدليات مفتوحة", "الآن مفتوحة"]:
        reply = get_open_pharmacies()
    else:
        reply = "👋 مرحبًا! أرسل:\n- 'جميع الصيدليات'\n- 'الصيدليات المفتوحة'"

    send_whatsapp_message(sender, reply)
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
