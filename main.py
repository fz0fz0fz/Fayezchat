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
    data = request.get_json() or {}
    sender  = (data.get("sender")  or "").strip()
    message = (data.get("message") or "").strip()

    if not sender or not message:
        return jsonify({"reply": "❗️ البيانات غير صحيحة."}), 400

    session = get_session(sender)
    text = message.strip().lower()

    # تمرير كل الرسائل الخاصة بالمنبه أو الجلسات إلى reminder.py
    if (
        session in {"reminder_menu", "oil_change_duration", "istighfar_interval"} or
        text in {"20", "٢٠", "منبه", "منبّه", "تذكير", "00"}
    ):
        result = handle_reminder(message, sender)
        return jsonify(result)

    # 0️⃣ رجوع للقائمة الرئيسية
    if text in {"0", "رجوع", "عودة", "القائمة"}:
        set_session(sender, None)
        return jsonify({"reply": MAIN_MENU_TEXT})

    # ⚠️ رد افتراضي
    return jsonify({
        "reply": "👋 أهلاً! أرسل:\n0 للقائمة الرئيسية\n20 للمنبّه"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
