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

# بيانات Whapi
WHAPI_API_URL = "https://gate.whapi.cloud"
WHAPI_TOKEN = "vlMGBHJpxhwRfTZzeNWXRP8CCa1Rteq4"

# دالة إرسال رسالة عبر Whapi
def send_whatsapp_message(phone, message):
    url = f"{WHAPI_API_URL}/v1/messages"
    headers = {
        "Authorization": f"Bearer {WHAPI_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": phone,
        "type": "text",
        "text": {
            "body": message
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        logging.info(f"تم إرسال الرد إلى {phone}: {message}")
        return response.json()
    except Exception as e:
        logging.error(f"خطأ أثناء إرسال الرسالة: {e}")
        return None

# نقطة الاستقبال من Whapi
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    logging.debug(f"تم الاستلام: {data}")

    message_obj = data.get("message", {})
    message_text = message_obj.get("text", "").strip()
    sender = data.get("from")

    if not message_text or not sender:
        return jsonify({"status": "ignored", "reason": "missing message or sender"})

    message_lower = message_text.lower()

    if message_lower in ["جميع الصيدليات", "كل الصيدليات"]:
        reply = get_all_pharmacies()
    elif message_lower in ["الصيدليات المفتوحة", "صيدليات مفتوحة", "الآن مفتوحة"]:
        reply = get_open_pharmacies()
    else:
        reply = "👋 مرحبًا! أرسل:\n- 'جميع الصيدليات'\n- 'الصيدليات المفتوحة'"

    send_whatsapp_message(sender, reply)
    return jsonify({"status": "success"})

@app.route("/", methods=["GET"])
def home():
    return "✅ Whapi bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
