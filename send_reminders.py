# send_reminders.py
import sqlite3
import os
from datetime import datetime
import requests
import logging

# تهيئة السجل (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# بيانات UltraMsg من متغيرات البيئة
INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")
TOKEN = os.getenv("ULTRAMSG_TOKEN")

if not INSTANCE_ID or not TOKEN:
    logging.error("❌ UltraMsg credentials not set in environment variables.")
    API_URL = ""
else:
    API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

DB_PATH = "reminders.db"

def send_due_reminders():
    """
    Check for due reminders in the database and send messages to users.
    Returns a summary of sent reminders.
    """
    if not API_URL:
        return {"sent_count": 0, "error": "UltraMsg credentials not set."}

    now = datetime.now().strftime("%Y-%m-%d")
    sent_count = 0
    errors = []

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # جلب التذكيرات المستحقة (remind_at أقل من أو يساوي التاريخ الحالي)
        c.execute("""
            SELECT id, user_id, type, message, remind_at
            FROM reminders
            WHERE remind_at <= ?
        """, (now,))
        reminders = c.fetchall()

        for reminder_id, user_id, reminder_type, custom_message, remind_at in reminders:
            message = custom_message if custom_message else f"⏰ تذكير: {reminder_type} الآن."
            if reminder_type == "موعد":
                message = "🩺 تذكير: غدًا موعد زيارتك للمستشفى أو مناسبتك. نتمنى لك التوفيق! 🌿"

            # إرسال الرسالة عبر UltraMsg
            try:
                response = requests.post(API_URL, data={
                    "token": TOKEN,
                    "to": user_id,
                    "body": message
                }, timeout=10)
                if response.status_code == 200:
                    sent_count += 1
                    logging.info(f"✅ تم إرسال تذكير لـ {user_id}: {reminder_type}")
                    # حذف التذكير بعد الإرسال (لأنه لمرة واحدة)
                    c.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
                else:
                    errors.append(f"Failed to send to {user_id}: {response.text}")
                    logging.error(f"❌ فشل إرسال تذكير لـ {user_id}: {response.text}")
            except Exception as e:
                errors.append(f"Error sending to {user_id}: {str(e)}")
                logging.error(f"❌ خطأ أثناء إرسال تذكير لـ {user_id}: {e}")

        conn.commit()
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
        logging.error(f"❌ خطأ في الوصول إلى قاعدة البيانات: {e}")
    finally:
        conn.close()

    return {"sent_count": sent_count, "errors": errors if errors else "No errors"}

if __name__ == "__main__":
    result = send_due_reminders()
    print(f"📤 عدد التذكيرات المرسلة: {result['sent_count']}")
    if result.get("errors") != "No errors":
        print(f"⚠️ الأخطاء: {result['errors']}")
