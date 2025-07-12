import logging
import os
from flask import Flask, request, jsonify
import requests
from services.session import get_session, set_session
from services.reminder import handle as handle_reminder, MAIN_MENU_TEXT

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# بيانات UltraMsg
ULTRAMSG_INSTANCE_ID = "instance130542"
ULTRAMSG_TOKEN = "pr2bhaor2vevcrts"
ULTRAMSG_API_URL = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"

def send_whatsapp_message(to, message):
    """إرسال رسالة واتساب عبر UltraMsg"""
    try:
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": to,
            "body": message
        }
        res = requests.post(ULTRAMSG_API_URL, data=payload)
        logging.info(f"📤 Sent to {to} | Status: {res.status_code} | Response: {res.text}")
    except Exception as e:
        logging.error(f"❌ Error sending message: {e}")

# ————————— Health-check —————————
@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# ————————— Webhook —————————
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True) or {}
        logging.info(f"📩 Received payload: {data}")

        sender = (data.get("from") or data.get("sender") or "").strip()
        message = (data.get("body") or data.get("message") or "").strip()

        if not sender or not message:
            logging.warning("❗️ Missing sender or message in payload.")
            return jsonify({"error": "Missing sender or message."}), 200  # لا ترجع 400 حتى لا يتوقف UltraMsg

        # 1) جلسة منبه
        session = get_session(sender)
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

# ————————— تشغيل السيرفر —————————
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
