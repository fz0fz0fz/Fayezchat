# send_reminders.py

import sqlite3
from datetime import datetime, timedelta
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

    # جلب التذكيرات المستحقة
    c.execute("""
        SELECT id, sender, type, interval_minutes 
        FROM reminders 
        WHERE active = 1 AND remind_at <= ?
    """, (now,))
    reminders = c.fetchall()

    for reminder_id, sender, reminder_type, interval in reminders:
        if reminder_type == "موعد":
            message = "🩺 تذكير: غدًا موعد زيارتك للمستشفى أو مناسبتك. نتمنى لك التوفيق! 🌿"
        else:
            message = f"⏰ تذكير: {reminder_type} الآن."

        # إرسال الرسالة عبر UltraMsg
        requests.post(API_URL, data={
            "token": TOKEN,
            "to": sender,
            "body": message
        })

        if interval:
            # إعادة جدولة التذكير التالي
            next_time = datetime.now() + timedelta(minutes=interval)
            c.execute("UPDATE reminders SET remind_at = ? WHERE id = ?", (next_time.strftime("%Y-%m-%d %H:%M:%S"), reminder_id))
            print(f"🔁 إعادة جدولة {reminder_type} لـ {sender} بعد {interval} دقيقة.")
        else:
            # إيقاف التذكير إذا كان لمرة واحدة
            c.execute("UPDATE reminders SET active = 0 WHERE id = ?", (reminder_id,))
            print(f"✅ تم إرسال تذكير لمرة واحدة لـ {sender}: {reminder_type}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    send_due_reminders()
