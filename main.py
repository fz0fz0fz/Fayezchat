import logging
import os
import requests
from flask import Flask, request, jsonify
from services.session import get_session, set_session
from services.reminder import handle as handle_reminder, MAIN_MENU_TEXT

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# بيانات UltraMsg
INSTANCE_ID = "instance130542"
TOKEN = "pr2bhaor2vevcrts"
ULTRAMSG_API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# دالة الإرسال لرقم واتساب
def send_whatsapp_message(to: str, message: str):
    payload = {
        "token": TOKEN,
        "to": to,
        "body": message
    }
    try:
        res = requests.post(ULTRAMSG_API_URL, data=payload)
        logging.info(f"📤 أُرسل إلى {to}: {message} | الحالة: {res.status_code}")
    except Exception as e:
        logging.error(f"❌ فشل الإرسال إلى {to}: {e}")

# ————————— Health-check —————————
@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# ————————— Webhook —————————
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    sender  = (data.get("sender")  or "").strip()
    message = (data.get("message") or "").strip()

    if not sender or not message:
        return jsonify({"reply": "❗️ البيانات غير صحيحة."}), 400

    # 1) لو في جلسة منبّه نشغّل منطق التذكير
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

    # 4) افتراضي
    reply = "👋 أهلاً! أرسل:\n0 للقائمة الرئيسية\n20 للمنبّه"
    send_whatsapp_message(sender, reply)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
