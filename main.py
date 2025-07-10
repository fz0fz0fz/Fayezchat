import logging
from flask import Flask, request, jsonify
import sqlite3
import requests
import os
from datetime import datetime, time

app = Flask(__name__)
DB_NAME = os.path.join(os.getcwd(), "services.db")

# إعداد التسجيل
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# بيانات Whapi
WHAPI_API_URL = "https://gate.whapi.cloud"
WHAPI_TOKEN = "vlMGBHJpxhwRfTZzeNWXRP8CCa1Rteq4"

# دالة إرسال رسالة عبر Whapi
def send_whatsapp_message(phone, message):
    url = f"{WHAPI_API_URL}/v1/messages"
    headers = {
        "Authorization": f"Bearer {WHAPI_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": phone,
        "type": "text",
        "text": {
            "body": message
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        logging.info(f"تم إرسال الرد إلى {phone}: {message}")
        return response.json()
    except Exception as e:
        logging.error(f"خطأ أثناء إرسال الرسالة: {e}")
        return None

# دالة جلب جميع الصيدليات من قاعدة البيانات
def get_all_pharmacies():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, description FROM categories")
    rows = c.fetchall()
    conn.close()
    if not rows:
        return "❌ لا توجد صيدليات مسجلة حاليًا."
    result = "📋 قائمة الصيدليات:\n"
    for name, desc in rows:
        result += f"\n🏪 {name}\n{desc}\n"
    return result

# دالة جلب الصيدليات المفتوحة حاليًا
def get_open_pharmacies():
    now = datetime.now().time()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time FROM categories")
    rows = c.fetchall()
    conn.close()

    open_now = []
    for row in rows:
        name, desc, m_start, m_end, e_start, e_end = row
        if m_start and m_end:
            m_start_time = datetime.strptime(m_start, "%H:%M").time()
            m_end_time = datetime.strptime(m_end, "%H:%M").time()
            if m_start_time <= now <= m_end_time:
                open_now.append((name, desc))
                continue
        if e_start and e_end:
            e_start_time = datetime.strptime(e_start, "%H:%M").time()
            e_end_time = datetime.strptime(e_end, "%H:%M").time()
            if e_start_time <= now <= e_end_time:
                open_now.append((name, desc))

    if not open_now:
        return "❌ لا توجد صيدليات مفتوحة حاليًا."

    result = "✅ الصيدليات المفتوحة الآن:\n"
    for name, desc in open_now:
        result += f"\n🏪 {name}\n{desc}\n"
    return result

# نقطة الاستقبال من Whapi (تم تعديل المسار)
@app.route("/webhook/messages", methods=["POST"])
def webhook():
    data = request.json
    logging.debug(f"تم الاستلام: {data}")

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

@app.route("/", methods=["GET"])
def home():
    return "✅ Whapi bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
