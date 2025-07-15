import logging
import os
from flask import Flask, request, jsonify
from services.reminder import handle as handle_reminder, init_reminder_db
from send_reminders import send_due_reminders

app = Flask(__name__)

# تهيئة السجل (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# إنشاء جدول التذكيرات إن لم يكن موجودًا
init_reminder_db()

@app.route("/")
def index():
    return "خدمة واتساب بوت تعمل ✅"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payload = request.get_json(force=True, silent=True) or {}
        logging.info(f"📥 Raw webhook data: {payload}")
        
        event_type = payload.get("event_type")
        if event_type != "message_received":
            logging.info(f"🚨 تم تجاهل الحدث: {event_type}")
            return jsonify({"status": "ignored"}), 200

        data = payload.get("data", {})
        message = (data.get("body") or "").strip()
        sender = (data.get("from") or "").strip()

        if not message or not sender:
            logging.warning(f"🚨 تم تجاهل رسالة ناقصة: {data}")
            return jsonify({"status": "ignored"}), 200

        logging.info(f"📥 Received message from {sender}: {message}")

        response = handle_reminder(sender, message)

        if response and "text" in response:
            success = send_whatsapp_message(sender, response["text"])
            logging.info(f"📤 Sent response to {sender}: {'Success' if success else 'Failed'}")
            return jsonify({"status": "sent" if success else "send_failed"}), 200

        return jsonify({"status": "no_action"}), 200
    except Exception as e:
        logging.exception(f"❌ Error processing request: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/send_reminders", methods=["GET", "POST"])
def send_reminders_endpoint():
    try:
        result = send_due_reminders()
        logging.info(f"📤 تم فحص التذكيرات وإرسالها: {result}")
        return jsonify({"status": "success", "details": result}), 200
    except Exception as e:
        logging.error(f"❌ خطأ أثناء إرسال التذكيرات: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def send_whatsapp_message(to: str, body: str) -> bool:
    import requests
    INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")
    TOKEN = os.getenv("ULTRAMSG_TOKEN")
    
    if not INSTANCE_ID or not TOKEN:
        logging.error("❌ UltraMsg credentials not set in environment variables.")
        return False

    URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"
    payload = {"token": TOKEN, "to": to, "body": body}

    try:
        res = requests.post(URL, data=payload, timeout=15)
        logging.info(f"📤 Message sent: {res.status_code} | {res.text}")
        return res.status_code == 200
    except Exception as e:
        logging.error(f"❌ Failed to send message: {e}")
        return False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
