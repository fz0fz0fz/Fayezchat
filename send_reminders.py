# send_reminders.py
import sqlite3
import os
from datetime import datetime, timedelta
import requests
import logging
import time

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

    # الحصول على الوقت الحالي بتوقيت UTC وإضافة 3 ساعات (UTC+3)
    now_utc = datetime.utcnow()  # الوقت بتوقيت UTC
    now_dt = now_utc + timedelta(hours=3)  # ضبط إلى UTC+3 (مثل توقيت السعودية)
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"🕒 Current time adjusted to UTC+3: {now}")
    logging.info(f"🕒 UTC time for reference: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    
    sent_count = 0
    errors = []
    processed_reminders = set()  # لتتبع التذكيرات التي تم معالجتها في هذه الجلسة

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # جلب التذكيرات المستحقة (remind_at أقل من أو يساوي الوقت الحالي المُعدل)
        c.execute("""
            SELECT id, user_id, reminder_type, message, remind_at, interval_days
            FROM reminders
            WHERE active = 1 AND remind_at <= ?
        """, (now,))
        reminders = c.fetchall()
        
        logging.info(f"🔍 Found {len(reminders)} due reminders at {now}")

        if not reminders:
            logging.info(f"✅ No due reminders found at {now}")
            # للتحقق من التذكيرات القادمة (للتأكد من أنها موجودة)
            c.execute("SELECT id, user_id, reminder_type, remind_at FROM reminders WHERE active = 1")
            all_reminders = c.fetchall()
            logging.info(f"📋 Total active reminders in database: {len(all_reminders)}")
            for reminder in all_reminders:
                logging.info(f"📅 Active reminder {reminder[0]} for {reminder[1]} at {reminder[3]} (Type: {reminder[2]})")
        else:
            for reminder in reminders:
                reminder_id, user_id, reminder_type, custom_message, remind_at_str, interval_days = reminder
                
                # تجاهل التذكير إذا تم معالجته في هذه الجلسة
                if reminder_id in processed_reminders:
                    logging.info(f"⚠️ Skipping already processed reminder {reminder_id} for {user_id}")
                    continue
                
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

                # إرسال الرسالة عبر UltraMsg مع إعادة المحاولة
                try:
                    logging.info(f"📤 Trying to send message to {user_id}: {message[:50]}...")
                    success = False
                    for attempt in range(3):  # محاولة إرسال الرسالة حتى 3 مرات
                        try:
                            response = requests.post(API_URL, data={
                                "token": TOKEN,
                                "to": user_id,
                                "body": message
                            }, timeout=10)
                            if response.status_code == 200:
                                sent_count += 1
                                logging.info(f"✅ تم إرسال تذكير لـ {user_id}: {reminder_type} في المحاولة {attempt + 1}")
                                success = True
                                break  # توقف إذا نجح الإرسال
                            else:
                                logging.error(f"❌ فشل إرسال تذكير لـ {user_id} في المحاولة {attempt + 1}: Status {response.status_code}, Response: {response.text[:100]}...")
                                if attempt < 2:  # انتظر فقط في المحاولات غير الأخيرة
                                    time.sleep(5)  # انتظر 5 ثواني قبل المحاولة التالية
                        except requests.exceptions.RequestException as e:
                            logging.error(f"❌ خطأ في الاتصال في المحاولة {attempt + 1} لـ {user_id}: {str(e)}")
                            if attempt < 2:
                                time.sleep(5)
                    if not success:
                        errors.append(f"Failed to send to {user_id} after 3 attempts")
                        logging.error(f"❌ فشل إرسال تذكير لـ {user_id} بعد 3 محاولات")
                    else:
                        # إضافة التذكير إلى مجموعة المعالجة لتجنب التكرار في نفس الجلسة
                        processed_reminders.add(reminder_id)
                        
                        # تحديث إحصائيات التذكيرات المرسلة (باستخدام INSERT ... ON CONFLICT)
                        try:
                            c.execute('''
                                INSERT INTO reminder_stats (user_id, reminders_sent)
                                VALUES (?, 1)
                                ON CONFLICT(user_id) DO UPDATE SET reminders_sent = reminders_sent + 1
                            ''', (user_id,))
                            logging.info(f"📊 Updated stats for {user_id}")
                        except Exception as e:
                            logging.error(f"❌ Error updating stats for {user_id}: {str(e)}")
                            errors.append(f"Error updating stats for {user_id}: {str(e)}")
                        
                        if interval_days > 0:
                            # إعادة جدولة التذكير التالي
                            try:
                                next_time = remind_at + timedelta(days=interval_days)
                                c.execute("UPDATE reminders SET remind_at = ? WHERE id = ?", 
                                          (next_time.strftime("%Y-%m-%d %H:%M:%S"), reminder_id))
                                conn.commit()  # التأكد من Commit بعد كل عملية UPDATE
                                logging.info(f"🔁 إعادة جدولة {reminder_type} لـ {user_id} بعد {interval_days} يوم/أيام إلى {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            except Exception as e:
                                logging.error(f"❌ Error rescheduling reminder {reminder_id}: {str(e)}")
                                errors.append(f"Error rescheduling reminder {reminder_id}: {str(e)}")
                        else:
                            # إيقاف التذكير إذا كان لمرة واحدة
                            try:
                                c.execute("UPDATE reminders SET active = 0 WHERE id = ?", (reminder_id,))
                                conn.commit()  # التأكد من Commit بعد كل عملية UPDATE
                                logging.info(f"✅ تم إرسال تذكير لمرة واحدة لـ {user_id}: {reminder_type}")
                            except Exception as e:
                                logging.error(f"❌ Error deactivating reminder {reminder_id}: {str(e)}")
                                errors.append(f"Error deactivating reminder {reminder_id}: {str(e)}")
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
