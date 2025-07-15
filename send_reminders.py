import psycopg2
import os
import requests
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
DB_URL = os.getenv("DATABASE_URL")
API_URL = f"https://api.ultramsg.com/{os.getenv('ULTRAMSG_INSTANCE_ID')}/messages/chat"
TOKEN = os.getenv("ULTRAMSG_TOKEN")

def send_due_reminders():
    if not DB_URL or not TOKEN:
        logging.error("❌ DATABASE_URL or ULTRAMSG_TOKEN not set.")
        return {"sent_count": 0, "errors": ["Missing environment variables"]}
    
    now_utc = datetime.now(pytz.UTC)
    now_dt = now_utc.astimezone(pytz.timezone("Asia/Riyadh"))
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    sent_count = 0
    errors = []
    processed_reminders = set()
    
    try:
        conn = psycopg2.connect(DB_URL)
        c = conn.cursor()
        c.execute('''
            SELECT id, user_id, reminder_type, message, remind_at, interval_days
            FROM reminders
            WHERE active = TRUE AND remind_at <= %s
        ''', (now,))
        reminders = c.fetchall()
        
        session = requests.Session()
        for reminder in reminders:
            reminder_id, user_id, reminder_type, message, remind_at, interval_days = reminder
            if reminder_id in processed_reminders:
                continue
            processed_reminders.add(reminder_id)
            
            if not user_id.startswith('+') and '@' not in user_id:
                user_id = f"+{user_id}"
            
            for attempt in range(3):
                try:
                    response = session.post(API_URL, data={
                        "token": TOKEN,
                        "to": user_id,
                        "body": f"⏰ تذكير: {reminder_type}\n{message}"
                    }, timeout=10)
                    if response.status_code == 200:
                        sent_count += 1
                        logging.info(f"✅ تم إرسال تذكير لـ {user_id}: {reminder_type}")
                        c.execute('UPDATE reminders SET remind_at = %s WHERE id = %s', 
                                  (remind_at + timedelta(days=interval_days) if interval_days > 0 else remind_at, reminder_id))
                        if interval_days == 0:
                            c.execute('UPDATE reminders SET active = FALSE WHERE id = %s', (reminder_id,))
                        c.execute('''
                            INSERT INTO reminder_stats (user_id, reminders_sent)
                            VALUES (%s, 1)
                            ON CONFLICT (user_id) DO UPDATE SET reminders_sent = reminder_stats.reminders_sent + 1
                        ''', (user_id,))
                        conn.commit()
                        break
                    else:
                        logging.error(f"❌ فشل إرسال تذكير لـ {user_id}: {response.text}")
                        if attempt == 2:
                            errors.append(f"Failed to send to {user_id}: {response.text}")
                except requests.RequestException as e:
                    logging.error(f"❌ خطأ أثناء إرسال تذكير لـ {user_id}: {e}")
                    if attempt == 2:
                        errors.append(f"Failed to send to {user_id}: {str(e)}")
                    time.sleep(5)
    
        return {"sent_count": sent_count, "errors": errors}
    except psycopg2.DatabaseError as e:
        logging.error(f"❌ Database error: {e}")
        return {"sent_count": 0, "errors": [f"Database error: {str(e)}"]}
    finally:
        if conn is not None:
            conn.close()
            logging.info("🔒 Database connection closed")
