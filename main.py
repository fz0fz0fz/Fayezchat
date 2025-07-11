import logging
from flask import Flask, request
import os
from services.reminder import handle as handle_reminder

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    logging.info(f"Received data: {data}")

    message = data.get("message", "").strip()
    sender = data.get("sender", "")

    if not message or not sender:
        return "Invalid data", 400

    if message == "0":
        return send_main_menu(sender)

    # استدعاء خدمة المنبه فقط
    if handle_reminder(sender, message):
        return "OK", 200

    return "No action taken", 200

def send_main_menu(sender):
    main_menu = """📝 *أهلا بك في دليل خدمات القرين*

يمكنك الاستعلام عن الخدمات التالية:

1️⃣ حكومي🏢  
2️⃣ صيدلية💊  
3️⃣ بقالة🥤  
4️⃣ خضار🥬  
5️⃣ رحلات⛺️  
6️⃣ حلا🍮  
7️⃣ أسر منتجة🥧  
8️⃣ مطاعم🍔  
9️⃣ قرطاسية📗  
🔟 محلات 🏪
11️⃣ شالية  
12️⃣ وايت  
13️⃣ شيول  
14️⃣ دفان  
15️⃣ مواد بناء وعوازل  
16️⃣ عمال  
17️⃣ محلات  
18️⃣ ذبائح وملاحم  
19️⃣ نقل مدرسي ومشاوير  
20️⃣ منبه⏰
"""
    send_whatsapp_message(sender, main_menu)
    return "Menu sent", 200

def send_whatsapp_message(to, message):
    import requests
    ULTRAMSG_INSTANCE_ID = os.environ.get("ULTRAMSG_INSTANCE_ID", "instance130542")
    ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN", "pr2bhaor2vevcrts")
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    payload = {
        "to": to,
        "body": message
    }
    headers = {
        "content-type": "application/json",
        "DNT": "1",
        "Authorization": f"Bearer {ULTRAMSG_TOKEN}"
    }
    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent message to {to}, response: {response.text}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
