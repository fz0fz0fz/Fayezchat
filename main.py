import logging
from flask import Flask, request, jsonify
import sqlite3
import requests
import os
from datetime import datetime, time

app = Flask(__name__)
DB_NAME = os.path.join(os.getcwd(), "services.db")

# إعداد التسجيل
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

ULTRAMSG_INSTANCE_ID = os.environ.get("ULTRAMSG_INSTANCE_ID", "instance130542")
ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN", "pr2bhaor2vevcrts")

# ========== قاعدة البيانات ==========
def get_all_pharmacies():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, description FROM categories")
        rows = c.fetchall()
        conn.close()

        if not rows:
            return "❌ لا توجد بيانات حالياً."

        response = "📋 قائمة الصيدليات:\n\n"
        for row in rows:
            response += f"🏥 {row[0]}\n{row[1]}\n\n"
        return response.strip()
    except Exception as e:
        logging.error(f"خطأ أثناء جلب الصيدليات: {e}")
        return "حدث خطأ أثناء جلب البيانات."

def get_open_pharmacies():
    now = datetime.now().time()
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time FROM categories")
        rows = c.fetchall()
        conn.close()

        open_now = []
        for row in rows:
            name, desc, m_start, m_end, e_start, e_end = row
            if (m_start and m_end and time.fromisoformat(m_start) <= now <= time.fromisoformat(m_end)) or \
               (e_start and e_end and time.fromisoformat(e_start) <= now <= time.fromisoformat(e_end)):
                open_now.append(f"🏥 {name}\n{desc}")

        if not open_now:
            return "❌ لا توجد صيدليات مفتوحة الآن."

        return "🚪 الصيدليات المفتوحة الآن:\n\n" + "\n\n".join(open_now)
    except Exception as e:
        logging.error(f"خطأ أثناء جلب الصيدليات المفتوحة: {e}")
        return "حدث خطأ أثناء جلب البيانات."

# ========== إرسال الرد ==========
def send_whatsapp_message(to, message):
    try:
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        payload = {"to": to, "body": message}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers, params={"token": ULTRAMSG_TOKEN})
        logging.info(f"تم إرسال الرد: {response.text}")
    except Exception as e:
        logging.error(f"خطأ أثناء إرسال الرسالة: {e}")

# ========== Webhook للـ Whapi ==========
@app.route("/webhook/messages/post", methods=["POST"])
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

# ========== التشغيل المحلي ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
