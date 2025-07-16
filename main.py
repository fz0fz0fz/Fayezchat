from flask import Flask, request, jsonify
import requests
import logging
import os
from dotenv import load_dotenv
from services import handle_reminder, init_reminder_db, init_session_db
from services.send_reminders import send_due_reminders  # تأكد من الاستيراد

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TOKEN = os.getenv("ULTRAMSG_TOKEN")
INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")
API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

init_session_db()
init_reminder_db()

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
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"status": "error", "message": "Failed to connect to database"}), 500
        
        response = handle_reminder(user_id, message, conn)
        close_db_connection(conn)
        
        # تحويل datetime إلى سلسلة نصية إذا كان موجودًا
        if "remind_at" in response and isinstance(response["remind_at"], datetime):
            response["remind_at"] = response["remind_at"].astimezone(pytz.timezone("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M")
        
        text = response.get("text", "حدث خطأ، حاول مرة أخرى.")
        keyboard = response.get("keyboard", "")
        
        payload = {"token": TOKEN, "to": user_id, "body": text}
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

@app.route("/send_reminders", methods=["GET"])
def send_reminders():
    result = send_due_reminders()
    return jsonify({
        "status": "success" if result["sent_count"] > 0 else "partial_success" if not result["errors"] else "error",
        "sent_count": result["sent_count"],
        "errors": result["errors"]
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
