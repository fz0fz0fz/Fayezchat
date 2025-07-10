import logging
from flask import Flask, request, jsonify
import sqlite3
import requests
import os
from datetime import datetime

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

# دالة عرض جميع الصيدليات
def get_all_pharmacies():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, description FROM categories")
    result = c.fetchall()
    conn.close()
    return "\n\n".join([f"🏪 {row[0]}\n{row[1]}" for row in result])

# دالة عرض الصيدليات المفتوحة
def get_open_pharmacies():
    now = datetime.now().time()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT name, description, morning_start_time, morning_end_time,
               evening_start_time, evening_end_time
        FROM categories
    ''')
    result = c.fetchall()
    conn.close()

    open_now = []
    for row in result:
        name, description, m_start, m_end, e_start, e_end = row
        m_start = datetime.strptime(m_start, "%H:%M").time()
        m_end = datetime.strptime(m_end, "%H:%M").time()
        e_start = datetime.strptime(e_start, "%H:%M").time()
        e_end = datetime.strptime(e_end, "%H:%M").time()

        if (m_start <= now <= m_end) or (e_start <= now <= e_end):
            open_now.append(f"🏪 {name}\n{description}")

    return "\n\n".join(open_now) if open_now else "🚫 لا توجد صيدليات مفتوحة الآن."

# نقطة الاستقبال من Whapi
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    logging.debug(f"تم الاستلام: {data}")

    message_obj = data.get("data", {})
    message_text = message_obj.get("text", {}).get("body", "").strip()
    sender = message_obj.get("from")

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
