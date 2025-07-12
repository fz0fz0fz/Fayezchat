import logging
import os
from flask import Flask, request, jsonify
from services.session import get_session, set_session
from services.reminder import handle as handle_reminder, MAIN_MENU_TEXT
import requests

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# معلومات UltraMsg
ULTRAMSG_INSTANCE_ID = "instance130542"
ULTRAMSG_TOKEN = "pr2bhaor2vevcrts"
ULTRAMSG_API_URL = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"

# إرسال رد للواتساب
def send_whatsapp_message(to, message):
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": to,
        "body": message
    }
    try:
        res = requests.post(ULTRAMSG_API_URL, data=payload)
        logging.info(f"📤 Message sent: {res.status_code} | {res.text}")
    except Exception as e:
        logging.error(f"❌ Failed to send message: {e}")

# Health Check
@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True) or {}
        logging.info(f"📩 Received payload: {data}")

        # استخراج البيانات من داخل "data"
        payload_data = data.get("data", {})
        sender = (payload_data.get("from") or "").strip()
        message = (payload_data.get("body") or "").strip()

        if not sender or not message:
            logging.warning("❗️ Missing sender or message in payload.")
            return jsonify({"error": "Missing sender or message."}), 200

        session = get_session(sender)

        # 1) جلسة منبه نشطة
        if session and session.startswith("reminder"):
            result = handle_reminder(message, sender)
            send_whatsapp_message(sender, result["reply"])
            return jsonify({"status": "ok"})

        # 2) رجوع للقائمة الرئيسية
        if message in ["0", "رجوع", "عودة", "القائمة"]:
            set_session(sender, None)
            send_whatsapp_message(sender, MAIN_MENU_TEXT)
            return jsonify({"status": "ok"})

        # 3) دخول قائمة المنبّه
        if message in ["20", "٢٠", "منبه", "منبّه", "تذكير"]:
            result = handle_reminder(message, sender)
            send_whatsapp_message(sender, result["reply"])
            return jsonify({"status": "ok"})

        # 4) رد افتراضي
        reply = "👋 أهلاً! أرسل:\n0 للقائمة الرئيسية\n20 للمنبّه"
        send_whatsapp_message(sender, reply)
        return jsonify({"status": "ok"})

    except Exception as e:
        logging.exception("❌ Exception in webhook handler:")
        return jsonify({"error": str(e)}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
