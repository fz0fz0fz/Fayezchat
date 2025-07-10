import logging
from flask import Flask, request, jsonify
import sqlite3
import requests
import os
from datetime import datetime

app = Flask(__name__)
DB_NAME = os.path.join(os.getcwd(), "services.db")

# إعداد تسجيل السجلات
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# بيانات Whapi (ضع القيم الحقيقية هنا أو في env)
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN", "توكن_whapi")
WHAPI_INSTANCE_ID = os.getenv("WHAPI_INSTANCE_ID", "معرّف_whapi")

# إرسال رسالة واتساب
def send_whatsapp_message(phone, message):
    url = f"https://gate.whapi.cloud/instance{WHAPI_INSTANCE_ID}/sendMessage?token={WHAPI_TOKEN}"
    payload = {
        "phone": phone,
        "message": message
    }
    try:
        response = requests.post(url, json=payload)
        logging.debug(f"🔁 تم الإرسال إلى {phone}: {response.text}")
    except Exception as e:
        logging.error(f"❌ خطأ في الإرسال: {e}")

# استرجاع جميع الصيدليات
def get_all_pharmacies():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, description FROM categories")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "🚫 لا توجد صيدليات حالياً."
    result = "🏥 قائمة الصيدليات:\n\n"
    for name, desc in rows:
        result += f"📌 {name}\n{desc}\n\n"
    return result.strip()

# استرجاع الصيدليات المفتوحة حالياً
def get_open_pharmacies():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_hour = int(now.strftime("%H"))
    current_minute = int(now.strftime("%M"))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time FROM categories")
    rows = cursor.fetchall()
    conn.close()

    open_list = []

    for name, desc, m_start, m_end, e_start, e_end in rows:
        def time_in_range(start, end):
            try:
                start_hour, start_minute = map(int, start.split(":"))
                end_hour, end_minute = map(int, end.split(":"))
                now_minutes = current_hour * 60 + current_minute
                start_minutes = start_hour * 60 + start_minute
                end_minutes = end_hour * 60 + end_minute
                return start_minutes <= now_minutes <= end_minutes
            except:
                return False

        if time_in_range(m_start, m_end) or time_in_range(e_start, e_end):
            open_list.append(f"✅ {name}\n{desc}")

    if not open_list:
        return "🚫 لا توجد صيدليات مفتوحة حالياً."

    return "🏥 الصيدليات المفتوحة الآن:\n\n" + "\n\n".join(open_list)

# نقطة استقبال Webhook من Whapi
@app.route("/webhook/messages/<method>", methods=["POST", "PATCH", "PUT", "DELETE"])
def webhook_handler(method):
    data = request.json
    logging.debug(f"📩 [{method.upper()}] تم الاستلام: {data}")

    message_obj = data.get("message", {})
    message_text = message_obj.get("text", "").strip()
    sender = data.get("from")

    if not message_text or not sender:
        return jsonify({"status": "ignored", "reason": "missing message or sender"})

    message_lower = message_text.lower()

    if message_lower in ["جميع الصيدليات", "كل الصيدليات"]:
        reply = get_all_pharmacies()
    elif message_lower in ["الصيدليات المفتوحة", "صيدليات مفتوحة", "الآن مفتوحة"]:
        reply = get_open_pharmacies()
    else:
        reply = "👋 مرحبًا! أرسل:\n- 'جميع الصيدليات'\n- 'الصيدليات المفتوحة'"

    send_whatsapp_message(sender, reply)
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True)
