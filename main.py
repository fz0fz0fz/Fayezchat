import logging
import os

from flask import Flask, request, jsonify
from services.reminder import (
    handle as handle_reminder,
    init_reminder_db          # ← NEW
)
from services.session import get_session, set_session   # ستحتاجه لاحقاً إن توسّعت

app = Flask(__name__)

# ───────────────────────────────────────────
# تهيئة السجل
# ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ───────────────────────────────────────────
# (1) إنشـاء جـدول reminders إن لزم
# ───────────────────────────────────────────
init_reminder_db()

# ───────────────────────────────────────────
# (2) مسارات الـ Flask
# ───────────────────────────────────────────
@app.route("/")
def index():
    return "خدمة واتساب بوت تعمل ✅"

@app.route("/webhook", methods=["POST"])
def webhook():
    payload    = request.get_json(force=True, silent=True) or {}
    event_type = payload.get("event_type")

    # نتعامل فقط مع رسائل الدردشات
    if event_type != "message_received":
        return jsonify({"status": "ignored"}), 200

    data    = payload.get("data", {})
    message = (data.get("body")  or "").strip()
    sender  = (data.get("from")  or "").strip()

    # ✅ تجاهل الرسائل الناقصة ولا نوقف السيرفر
    if not message or not sender:
        logging.warning(f"🚨 تم تجاهل رسالة ناقصة: {data}")
        return jsonify({"status": "ignored"}), 200

    logging.info(f"📥 Received message from {sender}: {message}")

    # معالجة الطلب بمنطق التذكير
    response = handle_reminder(message, sender)

    # إرسال الرد إن وُجد
    if response and "reply" in response:
        send_whatsapp_message(sender, response["reply"])
        return jsonify({"status": "sent"}), 200

    return jsonify({"status": "no_action"}), 200


# ───────────────────────────────────────────
# (3) إرسال الرسائل عبر UltraMsg
# ───────────────────────────────────────────
def send_whatsapp_message(to: str, body: str):
    import requests

    INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID", "instance130542")
    TOKEN       = os.getenv("ULTRAMSG_TOKEN", "pr2bhaor2vevcrts")
    URL         = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

    payload = {"token": TOKEN, "to": to, "body": body}

    try:
        res = requests.post(URL, data=payload, timeout=15)
        logging.info(f"📤 Message sent: {res.status_code} | {res.text}")
    except Exception as e:
        logging.error(f"❌ Failed to send message: {e}")


# ───────────────────────────────────────────
# (4) نقطة تشغيل التطبيق
# ───────────────────────────────────────────
if __name__ == "__main__":
    # DEBUG ينبغي أن يكون False في بيئة الإنتاج
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
