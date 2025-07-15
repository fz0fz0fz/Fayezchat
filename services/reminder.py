import re
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional
from services.session import get_session, set_session
from services.db import get_categories
import logging

# تهيئة السجل (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# الحصول على DATABASE_URL من متغيرات البيئة
DB_URL = os.getenv("DATABASE_URL")

def init_reminder_db() -> None:
    """Initialize the database with necessary tables if not already created."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                message TEXT,
                remind_at TIMESTAMP NOT NULL,
                interval_days INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminder_stats (
                user_id TEXT PRIMARY KEY,
                reminders_sent INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        logging.info("✅ Database initialized successfully with PostgreSQL")
    except Exception as e:
        logging.error(f"❌ Error initializing database: {e}")
    finally:
        if conn is not None:
            conn.close()
            logging.info("🔒 Database connection closed during initialization")

def save_reminder(user_id: str, reminder_type: str, message: Optional[str], remind_at: str, interval_days: int = 0) -> bool:
    """Save a new reminder to the database."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return False
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, reminder_type, message, remind_at, interval_days, active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING id
        ''', (user_id, reminder_type, message, remind_at, interval_days))
        reminder_id = cursor.fetchone()[0]
        conn.commit()
        logging.info(f"✅ Reminder saved successfully for user {user_id}, ID: {reminder_id}, Type: {reminder_type}, At: {remind_at}, Interval: {interval_days} days")
        return True
    except Exception as e:
        logging.error(f"❌ Error saving reminder for user {user_id}: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for save_reminder user {user_id}")

def delete_all_reminders(user_id: str) -> bool:
    """Delete all reminders for a user from the database."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return False
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE user_id = %s", (user_id,))
        conn.commit()
        logging.info(f"✅ All reminders deleted for user {user_id}")
        return True
    except Exception as e:
        logging.error(f"❌ Error deleting reminders for user {user_id}: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for delete_all_reminders user {user_id}")

def get_current_reminders(user_id: str) -> list:
    """Retrieve all active reminders for a user."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return []
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, reminder_type, message, remind_at, interval_days FROM reminders WHERE user_id = %s AND active = TRUE ORDER BY remind_at", (user_id,))
        reminders = cursor.fetchall()
        result = []
        for reminder in reminders:
            reminder_id, r_type, msg, remind_at, interval_days = reminder
            result.append({
                "id": reminder_id,
                "type": r_type,
                "message": msg if msg else f"تذكير: {r_type}",
                "remind_at": remind_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(remind_at, datetime) else str(remind_at),
                "interval_days": interval_days
            })
        return result
    except Exception as e:
        logging.error(f"❌ Error retrieving reminders for user {user_id}: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for get_current_reminders user {user_id}")

def parse_time_arabic(text: str) -> Optional[datetime]:
    """Parse Arabic time expressions like 'بعد ساعة' or 'بعد 30 دقيقة' to a datetime object (UTC+3)."""
    now = datetime.now(pytz.UTC) + timedelta(hours=3)  # ضبط الوقت إلى UTC+3
    text = text.replace("أ", "ا").replace("إ", "ا")

    patterns = {
        r"بعد\s*(\d+)\s*(دقيقة|دقيقه|دقائق|minutes|minute)": lambda x: now + timedelta(minutes=int(x.group(1))),
        r"بعد\s*(\d+)\s*(ساعة|ساعه|ساعات|hours|hour)": lambda x: now + timedelta(hours=int(x.group(1))),
        r"بعد\s*(\d+)\s*(يوم|أيام|days|day)": lambda x: now + timedelta(days=int(x.group(1))),
        r"بعد\s*(\d+)\s*(اسبوع|أسابيع|weeks|week)": lambda x: now + timedelta(weeks=int(x.group(1))),
        r"اليوم\s*الساعة\s*(\d{1,2})(?::|\s*)(\d{2})?\s*(صباحا|صباحًا|مساءً|مساءا)?": lambda x: parse_today_time(x, now),
        r"غدا\s*الساعة\s*(\d{1,2})(?::|\s*)(\d{2})?\s*(صباحا|صباحًا|مساءً|مساءا)?": lambda x: parse_tomorrow_time(x, now),
    }

    text = re.sub(r"[\u200c\u200d]", "", text)
    for pattern, func in patterns.items():
        match = re.search(pattern, text)
        if match:
            return func(match).replace(tzinfo=None)  # إزالة معلومات المنطقة الزمنية لتخزينها كـ Naive Datetime
    return None

def parse_today_time(match, now):
    """Parse time for today like 'اليوم الساعة 8 مساءً'."""
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3) or ""
    if "مساء" in period and hour < 12:
        hour += 12
    today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return today

def parse_tomorrow_time(match, now):
    """Parse time for tomorrow like 'غدا الساعة 8 مساءً'."""
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3) or ""
    if "مساء" in period and hour < 12:
        hour += 12
    tomorrow = now + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return tomorrow

def parse_duration_to_seconds(text: str) -> int:
    """Parse duration text like 'كل 30 دقيقة' or 'كل يوم' to seconds."""
    text = text.replace("أ", "ا").replace("إ", "ا")
    total_seconds = 0
    patterns = [
        (r"(\d+)\s*(دقيقة|دقيقه|دقائق|minutes|minute)", 60),
        (r"(\d+)\s*(ساعة|ساعه|ساعات|hours|hour)", 3600),
        (r"(\d+)\s*(يوم|أيام|days|day)", 86400),
        (r"(\d+)\s*(اسبوع|أسابيع|weeks|week)", 604800),
    ]
    parts = []
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            value = int(match.group(1))
            total_seconds += value * multiplier
            parts.append(f"{value} {match.group(2)}")
    if parts:
        logging.info(f"🕒 Parsed duration '{text}' as {', '.join(parts)} = {total_seconds} seconds")
    else:
        logging.info(f"⚠️ Could not parse duration '{text}'")
    return total_seconds

def parse_interval_days(text: str) -> int:
    """Parse interval text like 'كل يوم' or 'كل 3 أيام' to number of days."""
    text = text.replace("أ", "ا").replace("إ", "ا")
    patterns = [
        (r"كل\s*(\d*)\s*(يوم|أيام|days|day)", lambda m: int(m.group(1)) if m.group(1) else 1),
        (r"كل\s*(\d*)\s*(اسبوع|أسابيع|weeks|week)", lambda m: int(m.group(1)) * 7 if m.group(1) else 7),
    ]
    for pattern, func in patterns:
        match = re.search(pattern, text)
        if match:
            days = func(match)
            logging.info(f"🔁 Parsed interval '{text}' as {days} days")
            return days
    return 0  # Default to 0 (no repeat) if no valid interval is found

def handle(chat_id: str, message_text: str) -> Dict[str, str]:
    """
    Handle reminder-related commands in the chat.
    Returns a dictionary with response message and optional custom keyboard.
    """
    user_id = chat_id
    response = {"text": "لم أفهم طلبك. حاول مرة أخرى.", "keyboard": ""}
    
    # جلب بيانات الجلسة (قد تكون None)
    session_data = get_session(user_id)
    if session_data is None:
        session_data = {}  # إذا كانت None، نبدأ بقاموس فارغ
        set_session(user_id, session_data)  # تهيئة جلسة جديدة إذا لم تكن موجودة
    
    current_state = session_data.get("state", "")

    # التعامل مع العودة إلى القائمة السابقة باستخدام "00"
    if message_text == "00":
        if current_state == "awaiting_reminder_time":
            session_data["state"] = "awaiting_reminder_category"
            set_session(user_id, session_data)
            categories = get_categories()
            keyboard = "||".join([f"{cat['emoji']} {cat['name']}" for cat in categories])
            response = {"text": "اختر نوع التذكير:", "keyboard": keyboard}
        elif current_state == "awaiting_reminder_message":
            session_data["state"] = "awaiting_reminder_time"
            set_session(user_id, session_data)
            reminder_type = session_data.get("reminder_type", "غير محدد")
            response = {"text": f"متى تريد أن أذكرك بـ '{reminder_type}'؟\n(مثال: بعد ساعة، اليوم الساعة 8 مساءً، غدا الساعة 2 ظهرًا)", "keyboard": ""}
        elif current_state == "awaiting_reminder_interval":
            session_data["state"] = "awaiting_reminder_message"
            set_session(user_id, session_data)
            response = {"text": "هل تريد إضافة رسالة مخصصة للتذكير؟ إذا لا، اكتب 'لا' أو 'تخطي'.", "keyboard": ""}
        else:
            response = {"text": "أنت بالفعل في القائمة الرئيسية. اكتب 'تذكير' لإضافة تذكير جديد.", "keyboard": ""}
        return response

    if "تذكير" in message_text or "تذكّرني" in message_text:
        session_data["state"] = "awaiting_reminder_category"
        set_session(user_id, session_data)
        categories = get_categories()
        keyboard = "||".join([f"{cat['emoji']} {cat['name']}" for cat in categories])
        response = {"text": "اختر نوع التذكير:", "keyboard": keyboard}
    elif current_state == "awaiting_reminder_category":
        categories = get_categories()
        selected_cat = next((cat for cat in categories if cat["name"] in message_text or any(cat["name"] == msg for msg in message_text.split())), None)
        if selected_cat:
            session_data["reminder_type"] = selected_cat["name"]
            session_data["state"] = "awaiting_reminder_time"
            set_session(user_id, session_data)
            response = {"text": f"متى تريد أن أذكرك بـ '{selected_cat['name']}؟\n(مثال: بعد ساعة، اليوم الساعة 8 مساءً، غدا الساعة 2 ظهرًا)", "keyboard": ""}
        else:
            response = {"text": "يرجى اختيار نوع التذكير من القائمة أدناه:", "keyboard": "||".join([f"{cat['emoji']} {cat['name']}" for cat in categories])}
    elif current_state == "awaiting_reminder_time":
        remind_at = parse_time_arabic(message_text)
        if remind_at:
            session_data["remind_at"] = remind_at.strftime("%Y-%m-%d %H:%M:%S")
            session_data["state"] = "awaiting_reminder_message"
            set_session(user_id, session_data)
            response = {"text": "هل تريد إضافة رسالة مخصصة للتذكير؟ إذا لا، اكتب 'لا' أو 'تخطي'.", "keyboard": ""}
        else:
            response = {"text": "لم أفهم الوقت. حاول مرة أخرى.\n(مثال: بعد ساعة، اليوم الساعة 8 مساءً)", "keyboard": ""}
    elif current_state == "awaiting_reminder_message":
        if message_text in ["لا", "تخطي", "no", "skip"]:
            session_data["message"] = None
        else:
            session_data["message"] = message_text
        session_data["state"] = "awaiting_reminder_interval"
        set_session(user_id, session_data)
        response = {"text": "هل تريد تكرار التذكير؟ (مثال: كل يوم، كل 3 أيام، كل أسبوع)\nإذا لا، اكتب 'لا'.", "keyboard": ""}
    elif current_state == "awaiting_reminder_interval":
        interval_days = 0
        if message_text not in ["لا", "no", "تخطي", "skip"]:
            interval_days = parse_interval_days(message_text)
        reminder_type = session_data.get("reminder_type", "غير محدد")
        remind_at_str = session_data.get("remind_at", "")
        message = session_data.get("message")
        if save_reminder(user_id, reminder_type, message, remind_at_str, interval_days):
            session_data["state"] = ""
            set_session(user_id, session_data)
            interval_text = f" (يتكرر كل {interval_days} يوم)" if interval_days > 0 else ""
            remind_at_display = remind_at_str if remind_at_str else "غير محدد"
            response = {"text": f"✅ تم إعداد تذكير بـ '{reminder_type}' في {remind_at_display}{interval_text}.\nيمكنك إلغاء التذكيرات باستخدام 'إلغاء التذكيرات'.", "keyboard": ""}
        else:
            response = {"text": "❌ حدث خطأ أثناء حفظ التذكير. حاول مرة أخرى.", "keyboard": ""}
    elif "إلغاء التذكيرات" in message_text or "الغاء التذكيرات" in message_text:
        if delete_all_reminders(user_id):
            response = {"text": "✅ تم إلغاء جميع التذكيرات الخاصة بك.", "keyboard": ""}
        else:
            response = {"text": "❌ حدث خطأ أثناء إلغاء التذكيرات. حاول مرة أخرى.", "keyboard": ""}
    elif "تنبيهاتي الحالية" in message_text:
        reminders = get_current_reminders(user_id)
        if not reminders:
            response = {"text": "لا توجد تذكيرات حالية لديك.", "keyboard": ""}
        else:
            response_text = "⏰ تذكيراتك الحالية:\n"
            for r in reminders:
                interval_text = f" (يتكرر كل {r['interval_days']} يوم)" if r['interval_days'] > 0 else ""
                response_text += f"- {r['type']}: {r['remind_at']}{interval_text}\n"
                if r['message'] and r['message'] != f"تذكير: {r['type']}":
                    response_text += f"  الرسالة: {r['message']}\n"
            response = {"text": response_text, "keyboard": ""}
    return response
