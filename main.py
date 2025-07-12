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
    sender = (data.get("from") or "").strip()
    message = (data.get("body") or "").strip()

    # ✅ طباعة لتشخيص أخطاء 400
    if not sender or not message:
        logging.warning(f"🚨 بيانات غير صالحة في Webhook: {data}")
        return jsonify({"error": "Invalid data", "received": data}), 400

    # 1) لو في جلسة منبّه نشغّل منطق التذكير
    session = get_session(sender)
    if session and session.startswith("reminder"):
        result = handle_reminder(message, sender)
        return jsonify(result)

    # 2) رجوع للقائمة الرئيسية
    if message in ["0", "رجوع", "عودة", "القائمة"]:
        set_session(sender, None)
        return jsonify({"reply": MAIN_MENU_TEXT})

    # 3) دخول قائمة المنبّه
    if message in ["20", "٢٠", "منبه", "منبّه", "تذكير"]:
        result = handle_reminder(message, sender)
        return jsonify(result)

    # 4) افتراضي
    return jsonify({
        "reply": "👋 أهلاً! أرسل:\n0 للقائمة الرئيسية\n20 للمنبّه"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
