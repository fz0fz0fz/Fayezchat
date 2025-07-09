from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ULTRAMSG_INSTANCE_ID = os.environ.get("ULTRAMSG_INSTANCE_ID", "instance130542")
ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN", "pr2bhaor2vevcrts")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    incoming_msg = data.get("data", {}).get("body", "").strip()
    sender = data.get("data", {}).get("from", "")

    greetings = ["سلام", "السلام", "السلام عليكم", "مرحبا", "اهلاً", "hi", "hello"]
    menu_keywords = ["القائمة", "0", "٠", ".", "start", "ابدأ"]
    open_keywords = ["فاتحة", "مفتوحة", "الآن", "وش الصيدلية", "الصيدليات المفتوحة", "الصيدلية الفاتحة"]

    main_menu = """*_أهلا بك في دليل خدمات القرين..._*  
(اكتب القائمة كاملة هنا كما وضعت سابقًا)"""

    reply_body = None

    if incoming_msg in greetings:
        reply_body = "وعليكم السلام ورحمة الله وبركاته 👋 كيف يمكنني مساعدتك؟"

    elif incoming_msg in menu_keywords:
        reply_body = main_menu

    elif incoming_msg in ["2", "صيدلية"]:
        from services.pharmacy_service import get_all_pharmacies
        reply_body = get_all_pharmacies()

    elif any(word in incoming_msg for word in open_keywords):
        from services.pharmacy_service import get_open_pharmacies
        reply_body = get_open_pharmacies()

    else:
        return jsonify({"status": "ignored"})

    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    headers = {"Content-Type": "application/json"}
    payload = {"to": sender, "body": reply_body}

    try:
        resp = requests.post(url, json=payload, params={"token": ULTRAMSG_TOKEN}, headers=headers)
        print("UltraMsg response:", resp.text)
    except Exception as e:
        print("Error sending message:", e)

    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True)
