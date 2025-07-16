import os import re import logging from datetime import datetime, timedelta import pytz

from flask import Flask, request, jsonify from flask.json import JSONEncoder import requests

from dotenv import load_dotenv from services import handle_reminder, init_reminder_db, init_session_db from services.send_reminders import send_due_reminders from services.db_pool import get_db_connection, close_db_connection from services.session import get_session, set_session from services.db import get_categories

Load environment variables

env_loaded = load_dotenv()

Configure Flask app

app = Flask(name)

Custom JSON encoder to handle datetime objects

tz = pytz.timezone("Asia/Riyadh") class DateTimeEncoder(JSONEncoder): def default(self, obj): if isinstance(obj, datetime): # Convert to Asia/Riyadh and output ISO format return obj.astimezone(tz).isoformat() return super().default(obj)

app.json_encoder = DateTimeEncoder

Logging configuration

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

WhatsApp API configuration

TOKEN = os.getenv("ULTRAMSG_TOKEN") INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID") API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

Initialize databases

init_session_db() init_reminder_db()

@app.route("/webhook", methods=["POST"]) def webhook(): try: data = request.get_json() if not data or not isinstance(data, dict): logging.error("❌ Invalid payload received") return jsonify({"status": "error", "message": "Invalid payload"}), 400

message = data.get("data", {}).get("body", "").strip()
    user_id = data.get("data", {}).get("from", "")
    if not message or not user_id:
        logging.error("❌ Missing message or user_id in payload")
        return jsonify({"status": "error", "message": "Missing message or user_id"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Failed to connect to database"}), 500

    # Handle reminder logic and ensure all datetime fields are converted
    response = handle_reminder(user_id, message, conn)
    # Single point of conversion for dicts containing datetime
    from services.send_reminders import convert_datetime  # reuse convert helper
    response = convert_datetime(response)

    # Prepare payload for WhatsApp API
    payload = {"token": TOKEN, "to": user_id, "body": response.get("text", "")}    
    if response.get("keyboard"):
        payload["keyboard"] = response["keyboard"]

    with requests.Session() as session:
        resp = session.post(API_URL, data=payload, timeout=10)
        if resp.status_code == 200:
            logging.info(f"✅ Sent response to {user_id}: {response.get('text')}")
            return jsonify({"status": "success"}), 200
        else:
            logging.error(f"❌ Failed to send response to {user_id}: {resp.text}")
            return jsonify({"status": "error", "message": resp.text}), 500

except Exception as e:
    logging.error(f"❌ Error in webhook: {e}")
    return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send_reminders", methods=["GET"]) def send_reminders(): result = send_due_reminders() return jsonify({ "status": "success" if result["sent_count"] > 0 else "partial_success" if not result["errors"] else "error", "sent_count": result["sent_count"], "errors": result["errors"] }), 200

if name == "main": app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

