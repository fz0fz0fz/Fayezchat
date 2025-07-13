# send_reminders.py
import sqlite3
import os
from datetime import datetime, timedelta
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

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sent_count = 0
    errors = []

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # جلب التذكيرات المستحقة (remind_at أقل من أو يساوي الوقت الحالي)
        c.execute("""
            SELECT id, user_id, reminder_type, message, remind_at, interval_days
            FROM reminders
            WHERE active = 1 AND remind_at <= ?
        """, (now,))
        reminders = c.fetchall()
        
        logging.info(f"🔍 Found {len(reminders)} due reminders at {now}")

        if not reminders:
            logging.info(f"✅ No due reminders found at {now}")
        else:
            for reminder in reminders:
                reminder_id, user_id, reminder_type, custom_message, remind_at_str, interval_days = reminder
                logging.info(f"📌 Processing reminder {reminder_id} for {user_id} at {remind_at_str} (Type: {reminder_type})")
                
                # تحقق من تنسيق الوقت
                try:
                    remind_at = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M:%S")
                    logging.info(f"🕒 Reminder time {remind_at_str} is valid")
                except ValueError:
                    logging.error(f"❌ Invalid time format for reminder {reminder_id}: {remind_at_str}")
                    errors.append(f"Invalid time format for reminder {reminder_id}")
                    continue  # تجاهل التذكير إذا كان تنسيق الوقت غير صحيح
                
                message = custom_message if custom_message else f"⏰ تذكير: {reminder_type} الآن."
                if reminder_type == "موعد" and not custom_message:
                    message = "🩺 تذكير: غدًا موعد زيارتك للمستشفى أو مناسبتك. نتمنى لك التوفيق! 🌿"

                # التحقق من تنسيق user_id (يمكن تعديله حسب الحاجة)
                if not user_id.startswith('+') and '@' not in user_id:
                    logging.error(f"❌ Invalid user_id format for reminder {reminder_id}: {user_id}")
                    errors.append(f"Invalid user_id format for reminder {reminder_id}")
                    continue  # تجاهل التذكير إذا كان تنسيق user_id غير صحيح

                # إرسال الرسالة عبر UltraMsg
                try:
                    logging.info(f"📤 Trying to send message to {user_id}: {message[:50]}...")
                    response = requests.post(API_URL, data={
                        "token": TOKEN,
                        "to": user_id,
                        "body": message
                    }, timeout=10)
                    if response.status_code == 200:
                        sent_count += 1
                        logging.info(f"✅ تم إرسال تذكير لـ {user_id}: {reminder_type}")
                        
                        # تحديث إحصائيات التذكيرات المرسلة
                        c.execute('''
                            INSERT OR UPDATE INTO reminder_stats (user_id, reminders_sent)
                            VALUES (?, COALESCE((SELECT reminders_sent FROM reminder_stats WHERE user_id = ?), 0) + 1)
                        ''', (user_id, user_id))
                        
                        if interval_days > 0:
                            # إعادة جدولة التذكير التالي
                            next_time = remind_at + timedelta(days=interval_days)
                            c.execute("UPDATE reminders SET remind_at = ? WHERE id = ?", 
                                      (next_time.strftime("%Y-%m-%d %H:%M:%S"), reminder_id))
                            logging.info(f"🔁 إعادة جدولة {reminder_type} لـ {user_id} بعد {interval_days} يوم/أيام.")
                        else:
                            # إيقاف التذكير إذا كان لمرة واحدة
                            c.execute("UPDATE reminders SET active = 0 WHERE id = ?", (reminder_id,))
                            logging.info(f"✅ تم إرسال تذكير لمرة واحدة لـ {user_id}: {reminder_type}")
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
