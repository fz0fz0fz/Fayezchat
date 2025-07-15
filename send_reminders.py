import psycopg2
import os
from datetime import datetime, timedelta
import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")
TOKEN = os.getenv("ULTRAMSG_TOKEN")

if not INSTANCE_ID or not TOKEN:
    logging.error("❌ UltraMsg credentials not set in environment variables.")
    API_URL = ""
else:
    API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

DB_URL = os.getenv("DATABASE_URL")

def send_due_reminders():
    if not API_URL:
        return {"sent_count": 0, "error": "UltraMsg credentials not set."}

    now_utc = datetime.utcnow()
    now_dt = now_utc + timedelta(hours=3)
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"🕒 Current time adjusted to UTC+3: {now}")
    logging.info(f"🕒 UTC time for reference: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    
    sent_count = 0
    errors = []
    processed_reminders = set()

    try:
        conn = psycopg2.connect(DB_URL)
        c = conn.cursor()

        c.execute("""
            SELECT id, user_id, reminder_type, message, remind_at, interval_days
            FROM reminders
            WHERE active = TRUE AND remind_at <= %s
        """, (now,))
        reminders = c.fetchall()
        
        logging.info(f"🔍 Found {len(reminders)} due reminders at {now}")

        if not reminders:
            logging.info(f"✅ No due reminders found at {now}")
            c.execute("SELECT id, user_id, reminder_type, remind_at, interval_days FROM reminders WHERE active = TRUE")
            all_reminders = c.fetchall()
            logging.info(f"📋 Total active reminders in database: {len(all_reminders)}")
            for reminder in all_reminders:
                logging.info(f"📅 Active reminder {reminder[0]} for {reminder[1]} at {reminder[3]} (Type: {reminder[2]}, Interval: {reminder[4]} days)")
        else:
            for reminder in reminders:
                reminder_id, user_id, reminder_type, custom_message, remind_at_str, interval_days = reminder
                
                if reminder_id in processed_reminders:
                    logging.info(f"⚠️ Skipping already processed reminder {reminder_id} for {user_id}")
                    continue
                
                logging.info(f"📌 Processing reminder {reminder_id} for {user_id} at {remind_at_str} (Type: {reminder_type}, Interval: {interval_days} days)")
                
                try:
                    remind_at = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M:%S")
                    logging.info(f"🕒 Reminder time {remind_at_str} is valid")
                except ValueError:
                    logging.error(f"❌ Invalid time format for reminder {reminder_id}: {remind_at_str}")
                    errors.append(f"Invalid time format for reminder {reminder_id}")
                    continue
                
                message = custom_message if custom_message else f"⏰ تذكير: {reminder_type} الآن."
                if reminder_type == "موعد" and not custom_message:
                    message = "🩺 تذكير: غدًا موعد زيارتك للمستشفى أو مناسبتك. نتمنى لك التوفيق! 🌿"

                if not user_id.startswith('+') and '@' not in user_id:
                    logging.error(f"❌ Invalid user_id format for reminder {reminder_id}: {user_id}")
                    errors.append(f"Invalid user_id format for reminder {reminder_id}")
                    continue

                try:
                    for attempt in range(3):
                        logging.info(f"📤 Trying to send message to {user_id}: {message[:50]}... (Attempt {attempt + 1})")
                        response = requests.post(API_URL, data={
                            "token": TOKEN,
                            "to": user_id,
                            "body": message
                        }, timeout=10)
                        if response.status_code == 200:
                            sent_count += 1
                            logging.info(f"✅ تم إرسال تذكير لـ {user_id}: {reminder_type}")
                            processed_reminders.add(reminder_id)
                            break
                        else:
                            logging.error(f"❌ فشل إرسال تذكير لـ {user_id} في المحاولة {attempt + 1}: {response.text}")
                            if attempt < 2:
                                time.sleep(5)
                    else:
                        errors.append(f"Failed to send to {user_id} after 3 attempts")
                        logging.error(f"❌ فشل إرسال تذكير لـ {user_id} بعد 3 محاولات")
                except Exception as e:
                    errors.append(f"Error sending to {user_id}: {str(e)}")
                    logging.error(f"❌ خطأ أثناء إرسال تذكير لـ {user_id}: {e}")

                if response.status_code == 200:
                    try:
                        c.execute('''
                            INSERT INTO reminder_stats (user_id, reminders_sent)
                            VALUES (%s, 1)
                            ON CONFLICT (user_id) DO UPDATE SET reminders_sent = reminder_stats.reminders_sent + 1
                        ''', (user_id,))
                        logging.info(f"📊 Updated stats for {user_id}")
                    except Exception as e:
                        logging.error(f"❌ Error updating stats for {user_id}: {str(e)}")
                        errors.append(f"Error updating stats for {user_id}: {str(e)}")
                    
                    if interval_days > 0:
                        try:
                            next_time = remind_at + timedelta(days=interval_days)
                            c.execute("UPDATE reminders SET remind_at = %s WHERE id = %s", 
                                      (next_time.strftime("%Y-%m-%d %H:%M:%S"), reminder_id))
                            conn.commit()
                            logging.info(f"🔁 إعادة جدولة {reminder_type} لـ {user_id} بعد {interval_days} يوم/أيام إلى {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        except Exception as e:
                            logging.error(f"❌ Error rescheduling reminder {reminder_id}: {str(e)}")
                            errors.append(f"Error rescheduling reminder {reminder_id}: {str(e)}")
                    else:
                        try:
                            c.execute("UPDATE reminders SET active = FALSE WHERE id = %s", (reminder_id,))
                            conn.commit()
                            logging.info(f"❌ تم تعطيل التذكير {reminder_id} لـ {user_id} (غير متكرر)")
                        except Exception as e:
                            logging.error(f"❌ Error disabling reminder {reminder_id}: {str(e)}")
                            errors.append(f"Error disabling reminder {reminder_id}: {str(e)}")

        conn.commit()
        return {"sent_count": sent_count, "errors": "; ".join(errors) if errors else "No errors"}

    except Exception as e:
        logging.error(f"❌ Database error: {e}")
        return {"sent_count": sent_count, "errors": f"Database error: {str(e)}"}
    finally:
        if 'conn' in locals():
            conn.close()
            logging.info("🔒 Database connection closed")
