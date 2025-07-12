import logging
from flask import Flask, request, jsonify
import os
from services.reminder import handle as handle_reminder
from services.session import get_session, set_session

app = Flask(__name__)

# إعداد السجل
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.route("/")
def index():
    return "خدمة واتساب بوت تعمل ✅"

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.json
    event_type = payload.get("event_type")

    if event_type != "message_received":
        return jsonify({"status": "ignored"}), 200

    data = payload.get("data", {})
    message = data.get("body")
    sender = data.get("from")

    # ✅ تجاهل الرسائل الناقصة بدون إيقاف السيرفر
    if not message or not sender:
        logging.warning(f"🚨 تم تجاهل رسالة ناقصة: {data}")
        return jsonify({"status": "ignored"}), 200

    message = message.strip()

    logging.info(f"📥 Received message from {sender}: {message}")

    # تحديد المعالج حسب الجلسة أو نوع الطلب
    session = get_session(sender)
    response = handle_reminder(message, sender)

    # إرسال الرد إن وُجد
    if response and "reply" in response:
        send_whatsapp_message(sender, response["reply"])
        return jsonify({"status": "sent"}), 200

    return jsonify({"status": "no_action"}), 200

def send_whatsapp_message(to, message):
    import requests
    ULTRAMSG_INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID", "instance130542")
    ULTRAMSG_TOKEN = os.getenv("ULTRAMSG_TOKEN", "pr2bhaor2vevcrts")
    ULTRAMSG_URL = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"

    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": to,
        "body": message
    }

    try:
        res = requests.post(ULTRAMSG_URL, data=payload)
        logging.info(f"📤 Message sent: {res.status_code} | {res.text}")
    except Exception as e:
        logging.error(f"❌ Failed to send message: {e}")

if __name__ == "__main__":
    app.run(debug=True)
