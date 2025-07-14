import re
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional
from services.session import get_session, set_session
from services.db import get_categories

# الحصول على DATABASE_URL من متغيرات البيئة
DB_URL = os.getenv("DATABASE_URL")

def init_reminder_db() -> None:
    """Initialize the database with necessary tables if not already created."""
    conn = None
    try:
        if not DB_URL:
            print("❌ DATABASE_URL not set in environment variables.")
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
        print("✅ Database initialized successfully with PostgreSQL")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        if conn is not None:
            conn.close()
            print("🔒 Database connection closed during initialization")

def save_reminder(user_id: str, reminder_type: str, message: Optional[str], remind_at: str, interval_days: int = 0) -> bool:
    """Save a new reminder to the database."""
    conn = None
    try:
        if not DB_URL:
            print("❌ DATABASE_URL not set in environment variables.")
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
        print(f"✅ Reminder saved successfully for user {user_id}, ID: {reminder_id}, Type: {reminder_type}, At: {remind_at}, Interval: {interval_days} days")
        return True
    except Exception as e:
        print(f"❌ Error saving reminder for user {user_id}: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            print(f"🔒 Database connection closed for save_reminder user {user_id}")

def delete_all_reminders(user_id: str) -> Dict[str, str]:
    """Delete all reminders for a specific user."""
    conn = None
    try:
        if not DB_URL:
            print("❌ DATABASE_URL not set in environment variables.")
            return {"reply": "❌ خطأ: لم يتم إعداد قاعدة البيانات.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM reminders WHERE user_id = %s', (user_id,))
        count = cursor.fetchone()[0]
        cursor.execute('DELETE FROM reminders WHERE user_id = %s', (user_id,))
        conn.commit()
        print(f"✅ All reminders ({count}) deleted for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return {"reply": "✅ تم حذف جميع التذكيرات الخاصة بك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    except Exception as e:
        print(f"❌ Error deleting reminders for user {user_id}: {e}")
        return {"reply": f"❌ خطأ أثناء حذف التذكيرات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        if conn is not None:
            conn.close()
            print(f"🔒 Database connection closed for delete_all_reminders user {user_id}")

def delete_reminder(user_id: str, reminder_id: int) -> Dict[str, str]:
    """Delete a specific reminder by ID for a user."""
    conn = None
    try:
        if not DB_URL:
            print("❌ DATABASE_URL not set in environment variables.")
            return {"reply": "❌ خطأ: لم يتم إعداد قاعدة البيانات.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT reminder_type, remind_at, interval_days FROM reminders WHERE user_id = %s AND id = %s', (user_id, reminder_id))
        reminder = cursor.fetchone()
        cursor.execute('DELETE FROM reminders WHERE user_id = %s AND id = %s', (user_id, reminder_id))
        conn.commit()
        if cursor.rowcount > 0:
            reminder_info = f"Type: {reminder[0]}, At: {reminder[1]}, Interval: {reminder[2]}" if reminder else "Unknown"
            print(f"✅ Reminder {reminder_id} deleted for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({reminder_info})")
            return {"reply": f"✅ تم حذف التذكير رقم {reminder_id} بنجاح.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            print(f"❌ Reminder {reminder_id} not found for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return {"reply": f"❌ التذكير رقم {reminder_id} غير موجود أو لا يخصك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    except Exception as e:
        print(f"❌ Error deleting reminder {reminder_id} for user {user_id}: {e}")
        return {"reply": f"❌ خطأ أثناء حذف التذكير: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        if conn is not None:
            conn.close()
            print(f"🔒 Database connection closed for delete_reminder user {user_id}")

def update_reminder(user_id: str, reminder_id: int, remind_at: Optional[str] = None, message: Optional[str] = None, interval_days: Optional[int] = None) -> Dict[str, str]:
    """Update specific fields of a reminder for a user."""
    conn = None
    try:
        if not DB_URL:
            print("❌ DATABASE_URL not set in environment variables.")
            return {"reply": "❌ خطأ: لم يتم إعداد قاعدة البيانات.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        updates = []
        values = []
        if remind_at:
            updates.append("remind_at = %s")
            values.append(remind_at)
        if message is not None:
            updates.append("message = %s")
            values.append(message)
        if interval_days is not None:
            updates.append("interval_days = %s")
            values.append(interval_days)
        if updates:
            values.extend([user_id, reminder_id])
            query = f"UPDATE reminders SET {', '.join(updates)} WHERE user_id = %s AND id = %s"
            cursor.execute(query, values)
            conn.commit()
            if cursor.rowcount > 0:
                print(f"✅ Reminder {reminder_id} updated for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                return {"reply": f"✅ تم تعديل التذكير رقم {reminder_id} بنجاح.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
            else:
                print(f"❌ Reminder {reminder_id} not found for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                return {"reply": f"❌ التذكير رقم {reminder_id} غير موجود أو لا يخصك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            return {"reply": "❌ لم يتم تقديم أي بيانات للتعديل.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    except Exception as e:
        print(f"❌ Error updating reminder {reminder_id} for user {user_id}: {e}")
        return {"reply": f"❌ خطأ أثناء تعديل التذكير: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        if conn is not None:
            conn.close()
            print(f"🔒 Database connection closed for update_reminder user {user_id}")

def list_user_reminders(user_id: str, sender: str) -> Dict[str, str]:
    """List all active reminders for a specific user from the database."""
    conn = None
    try:
        if not DB_URL:
            print("❌ DATABASE_URL not set in environment variables.")
            return {"reply": "❌ خطأ: لم يتم إعداد قاعدة البيانات.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT id, reminder_type, remind_at, interval_days FROM reminders WHERE user_id = %s AND active = TRUE', (user_id,))
        rows = cursor.fetchall()

        if not rows:
            reply = "📭 لا توجد أي تنبيهات نشطة حاليًا.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
            set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
            print(f"✅ No active reminders found for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return {"reply": reply}

        reply = "🔔 تنبيهاتك النشطة الحالية:\n\n"
        for row in rows:
            interval_text = f" (يتكرر كل {row[3]} يوم)" if row[3] > 0 else ""
            reply += f"رقم {row[0]} - {row[1]}{interval_text} في {row[2]}\n"
        reply += "\n📌 خيارات:\n- أرسل 'حذف <رقم>' لحذف تذكير (مثل: حذف 1)\n- أرسل 'تعديل <رقم>' لتعديل تذكير (مثل: تعديل 2)\n"
        reply += "↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        print(f"✅ Listed {len(rows)} active reminders for user {user_id} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return {"reply": reply}
    except Exception as e:
        reply = f"❌ خطأ أثناء عرض التذكيرات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        print(f"❌ Error listing reminders for user {user_id}: {e}")
        return {"reply": reply}
    finally:
        if conn is not None:
            conn.close()
            print(f"🔒 Database connection closed for list_user_reminders user {user_id}")

def get_user_stats(user_id: str, sender: str) -> Dict[str, str]:
    """Get statistics about reminders for a specific user."""
    conn = None
    try:
        if not DB_URL:
            print("❌ DATABASE_URL not set in environment variables.")
            return {"reply": "❌ خطأ: لم يتم إعداد قاعدة البيانات.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM reminders WHERE user_id = %s AND active = TRUE', (user_id,))
        active_count = cursor.fetchone()[0]
        cursor.execute('SELECT reminders_sent FROM reminder_stats WHERE user_id = %s', (user_id,))
        sent_row = cursor.fetchone()
        sent_count = sent_row[0] if sent_row else 0
        
        reply = f"📊 *إحصائياتك الشخصية:*\n- التذكيرات النشطة: {active_count}\n- التذكيرات المرسلة: {sent_count}\n\n"
        reply += "↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        print(f"✅ Retrieved stats for user {user_id}: Active={active_count}, Sent={sent_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return {"reply": reply}
    except Exception as e:
        reply = f"❌ خطأ أثناء عرض الإحصائيات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        print(f"❌ Error retrieving stats for user {user_id}: {e}")
        return {"reply": reply}
    finally:
        if conn is not None:
            conn.close()
            print(f"🔒 Database connection closed for get_user_stats user {user_id}")

# Menu texts for better organization
MAIN_MENU_TEXT = (
    "*أهلاً بك في دليل خدمات القرين*\n"
    "يمكنك الاستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي 🏢\n"
    "2️⃣ منبه 📆\n"
    "3️⃣ صيدليات 💊"
)

REMINDER_MENU_TEXT = (
    "⏰ *منبه*\n\n"
    "اختر نوع التذكير الذي تريده:\n\n"
    "1️⃣ موعد مستشفى أو مناسبة\n"
    "2️⃣ تذكير يومي\n"
    "3️⃣ تذكير أسبوعي\n"
    "4️⃣ تنبيهاتي الحالية\n"
    "5️⃣ إحصائياتي\n\n"
    "❌ لحذف جميع التنبيهات أرسل: حذف\n"
    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
)

def is_valid_date(date_text: str) -> Optional[Dict[str, int]]:
    """Validate if a given text is a valid date in DD-MM-YYYY format."""
    try:
        parts = [int(p) for p in re.split(r"[-./_\\\s]+", date_text.strip()) if p]
        if len(parts) != 3:
            return None
        day, month, year = parts
        if year < 100:
            year += 2000
        if not (1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 9999):
            return None
        return {"day": day, "month": month, "year": year}
    except (ValueError, IndexError):
        return None

def is_valid_time(time_text: str) -> Optional[Dict[str, int]]:
    """Validate if a given text is a valid time in HH:MM format."""
    try:
        parts = [int(p
