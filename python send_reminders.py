import sqlite3
from datetime import datetime
import requests

# بيانات UltraMsg
INSTANCE_ID = "instance130542"
TOKEN = "pr2bhaor2vevcrts"
API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

DB_PATH = "reminders.db"

def send_due_reminders():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, sender, type FROM reminders WHERE active = 1 AND remind_at <= ?", (now,))
    reminders = c.fetchall()

    for reminder_id, sender, reminder_type in reminders:
        message = f"⏰ تذكير: {reminder_type} اليوم."

        requests.post(API_URL, data={
            "token": TOKEN,
            "to": sender,
            "body": message
        })

        c.execute("UPDATE reminders SET active = 0 WHERE id = ?", (reminder_id,))
        print(f"✅ تم إرسال التذكير لـ {sender}: {reminder_type}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    send_due_reminders()
