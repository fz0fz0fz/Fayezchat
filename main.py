# main.py

import logging
import os
from flask import Flask, request, jsonify
from services.session import get_session, set_session
from services.reminder import handle as handle_reminder, MAIN_MENU_TEXT

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ————————— Health-check —————————
@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# ————————— Webhook —————————
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(force=True) or {}

    # استخراج البيانات من UltraMsg
    data   = payload.get("data", {})
    sender = (data.get("from")  or "").strip()
    body   = (data.get("body")  or "").strip()

    logging.info("📥 البيانات المستلمة من UltraMsg: %s", data)

    if not sender or not body:
        logging.warning("⚠️ Webhook دون معلومات كافية: %s", payload)
        return jsonify({"reply": "❗️ البيانات غير صحيحة."}), 400

    # 1) جلسة تابعة للمنبه
    session = get_session(sender)
    if session and session.startswith("reminder"):
        return jsonify(handle_reminder(body, sender))

    # 2) رجوع للقائمة الرئيسية
    if body in ["0", "رجوع", "عودة", "القائمة"]:
        set_session(sender, None)
        return jsonify({"reply": MAIN_MENU_TEXT})

    # 3) دخول قائمة المنبّه
    if body in ["20", "٢٠", "منبه", "منبّه", "تذكير"]:
        return jsonify(handle_reminder(body, sender))

    # 4) رد افتراضي
    return jsonify({
        "reply": "👋 أهلاً! أرسل:\n0 للقائمة الرئيسية\n20 للمنبّه"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
