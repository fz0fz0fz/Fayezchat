from flask import Flask, request, jsonify
import os
import requests
import logging
from services import handle_reminder, init_reminder_db, init_session_db
from send_reminders import send_due_reminders
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
API_URL = f"https://api.ultramsg.com/{os.getenv('ULTRAMSG_INSTANCE_ID')}/messages/chat"
TOKEN = os.getenv("ULTRAMSG_TOKEN")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            logging.error("❌ Invalid payload received")
            return jsonify({"status": "error", "message": "Invalid payload"}), 400
        
        message = data.get("data", {}).get("body", "").strip()
        user_id = data.get("data", {}).get("from", "")
        
        if not message or not user_id:
            logging.error("❌ Missing message or user_id in payload")
            return jsonify({"status": "error", "message": "Missing message or user_id"}), 400
        
        response = handle_reminder(user_id, message)
        text = response.get("text", "حدث خطأ، حاول مرة أخرى.")
        keyboard = response.get("keyboard", "")
        
        payload = {
            "token": TOKEN,
            "to": user_id,
            "body": text
        }
        if keyboard:
            payload["keyboard"] = keyboard
        
        with requests.Session() as session:
            resp = session.post(API_URL, data=payload, timeout=10)
            if resp.status_code == 200:
                logging.info(f"✅ Sent response to {user_id}: {text}")
                return jsonify({"status": "success"}), 200
            else:
                logging.error(f"❌ Failed to send response to {user_id}: {resp.text}")
                return jsonify({"status": "error", "message": resp.text}), 500
    except Exception as e:
        logging.error(f"❌ Error in webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send_reminders", methods=["GET", "POST"])
def send_reminders_endpoint():
    try:
        result = send_due_reminders()
        logging.info(f"📤 تم فحص التذكيرات وإرسالها: {result}")
        return jsonify({"status": "success", "details": result}), 200
    except Exception as e:
        logging.error(f"❌ خطأ أثناء إرسال التذكيرات: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    init_reminder_db()
    init_session_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
