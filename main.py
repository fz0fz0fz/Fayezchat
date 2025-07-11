import logging from flask import Flask, request, jsonify import sqlite3 import requests import os from services.government import handle_government_services from services.pharmacies import handle_pharmacy_services from services.oil_reminder import handle_oil_reminder_message from send_reminders import send_due_reminders

app = Flask(name)

إعدادات UltraMsg

ULTRAMSG_INSTANCE_ID = os.environ.get("ULTRAMSG_INSTANCE_ID", "instance130542") ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN", "pr2bhaor2vevcrts") API_URL = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"

greetings = ["السلام عليكم", "سلام", "هلا", "مرحبا"] menu_triggers = ["0", "القائمة", "المنيو"]

menu_message = """ 👋 أهلا بك في دليل خدمات القرين، اختر من القائمة:

1️⃣ حكومي🏢
2️⃣ صيدلية💊
3️⃣ تغيير الزيت 🛢️

أرسل الرقم المناسب أو كلمة الخدمة. """

services_map = { "1": handle_government_services, "١": handle_government_services, "2": handle_pharmacy_services, "٢": handle_pharmacy_services, "3": handle_oil_reminder_message, "٣": handle_oil_reminder_message, }

@app.route("/webhook", methods=["POST"]) def webhook(): data = request.get_json(force=True) sender = data.get("data", {}).get("from") msg = data.get("data", {}).get("body", "").strip()

if not sender or not msg:
    return jsonify({"success": False}), 200

normalized = msg.strip().lower()

if normalized in greetings:
    reply = "وعليكم السلام ورحمة الله وبركاته 👋"
elif normalized in menu_triggers:
    reply = menu_message
elif normalized in ["3", "٣", "تغيير الزيت"]:
    reply = handle_oil_reminder_message(msg, sender)
elif normalized in services_map:
    reply = services_map[normalized]()
else:
    reply = "🤖 لم أفهم، أرسل 0 لعرض القائمة."

requests.post(API_URL, data={"token": ULTRAMSG_TOKEN, "to": sender, "body": reply})
return jsonify({"success": True}), 200

@app.route("/run-reminders", methods=["GET"]) def run_reminders(): send_due_reminders() return jsonify({"status": "Reminders sent"})

if name == 'main': app.run(debug=True)

