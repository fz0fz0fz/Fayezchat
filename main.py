import logging
import os
import sqlite3
from flask import Flask, request, jsonify
from services.session import get_session, set_session
from services.reminder import handle as handle_reminder

app = Flask(__name__)

# ——————————————— Health-check ———————————————
@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# ——————————————— Webhook ———————————————
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}

    sender = (data.get("sender") or "").strip()
    message = (data.get("message") or "").strip()

    if not sender or not message:
        return jsonify({"reply": "حدث خطأ في البيانات المستلمة."}), 400

    # إذا في جلسة منصة منبّه
    session = get_session(sender)
    if session and session.startswith("reminder"):
        result = handle_reminder(message, sender)
        return jsonify(result)

    # الرجوع للقائمة الرئيسية
    if message in ["0", "رجوع", "عودة", "القائمة"]:
        from services.reminder import MAIN_MENU_TEXT
        return jsonify({"reply": MAIN_MENU_TEXT})

    # اختيار خدمة المنبّه
    if message in ["20", "٢٠", "منبه", "تذكير", "منبّه"]:
        result = handle_reminder(message, sender)
        return jsonify(result)

    # لو تحتاج الـ services الأخرى بالمستقبل،
    # استدعائها هنا بنفس الأسلوب، وإلاّ رُدّ افتراضي:
    return jsonify({"reply": "مرحبًا! أرسل رقم الخدمة أو اسمها للحصول على التفاصيل."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
