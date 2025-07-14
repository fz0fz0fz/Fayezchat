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
    try:
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
        conn.close()

def save_reminder(user_id: str, reminder_type: str, message: Optional[str], remind_at: str, interval_days: int = 0) -> bool:
    """Save a new reminder to the database."""
    try:
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
        conn.close()

def delete_all_reminders(user_id: str) -> Dict[str, str]:
    """Delete all reminders for a specific user."""
    try:
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
        conn.close()

def delete_reminder(user_id: str, reminder_id: int) -> Dict[str, str]:
    """Delete a specific reminder by ID for a user."""
    try:
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
        conn.close()

def update_reminder(user_id: str, reminder_id: int, remind_at: Optional[str] = None, message: Optional[str] = None, interval_days: Optional[int] = None) -> Dict[str, str]:
    """Update specific fields of a reminder for a user."""
    try:
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
        conn.close()

def list_user_reminders(user_id: str, sender: str) -> Dict[str, str]:
    """List all active reminders for a specific user from the database."""
    try:
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
        conn.close()

def get_user_stats(user_id: str, sender: str) -> Dict[str, str]:
    """Get statistics about reminders for a specific user."""
    try:
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
        conn.close()

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
        parts = [int(p) for p in re.split(r"[:\s]+", time_text.strip()) if p]
        if len(parts) != 2:
            return None
        hour, minute = parts
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return {"hour": hour, "minute": minute}
    except (ValueError, IndexError):
        return None

def handle(msg: str, sender: str) -> Dict[str, str]:
    """Main handler for processing user input and managing conversation flow."""
    # Initialize database on first interaction if needed
    try:
        conn = psycopg2.connect(DB_URL)
        conn.close()
        print(f"✅ Database connection successful, initializing if not exists...")
        init_reminder_db()
    except Exception as e:
        print(f"⚠️ Database connection error: {e}, initializing now...")
        init_reminder_db()
    
    text = msg.strip()
    session = get_session(sender) or {}
    current_menu = session.get("menu", "main")

    # Handle return to main menu
    if text == "0":
        set_session(sender, {"menu": "main", "last_menu": ""})
        return {"reply": MAIN_MENU_TEXT}

    # Handle back navigation
    if text == "00":
        last_menu = session.get("last_menu", "main")
        if last_menu == "" or last_menu == "main":
            set_session(sender, {"menu": "main", "last_menu": ""})
            return {"reply": MAIN_MENU_TEXT}
        elif last_menu == "reminder_main":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        elif last_menu == "reminder_date":
            set_session(sender, {
                "menu": "reminder_date",
                "last_menu": "reminder_main",
                "reminder_type": session.get("reminder_type", "موعد"),
                "interval_days": session.get("interval_days", 0)
            })
            return {"reply": f"📅 أرسل تاريخ التذكير بالميلادي (مثل: 17-08-2025):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        elif last_menu == "reminder_time":
            set_session(sender, {
                "menu": "reminder_time",
                "last_menu": "reminder_date",
                "reminder_type": session.get("reminder_type", "موعد"),
                "interval_days": session.get("interval_days", 0),
                "date": session.get("date", "")
            })
            return {"reply": f"⏰ أدخل وقت التذكير بالصيغة HH:MM (مثل: 15:30):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        elif last_menu == "reminder_message":
            set_session(sender, {
                "menu": "reminder_message",
                "last_menu": "reminder_time",
                "reminder_type": session.get("reminder_type", "موعد"),
                "interval_days": session.get("interval_days", 0),
                "date": session.get("date", ""),
                "time": session.get("time", "")
            })
            return {"reply": f"📝 أدخل رسالة مخصصة للتذكير (أو 'تخطي' إذا لا تريد):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            set_session(sender, {"menu": "main", "last_menu": ""})
            return {"reply": MAIN_MENU_TEXT}

    # Handle delete all reminders command
    if text.lower() == "حذف":
        result = delete_all_reminders(sender)
        set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
        return result

    # Handle delete specific reminder
    if text.lower().startswith("حذف "):
        try:
            reminder_id = int(text.split()[1])
            result = delete_reminder(sender, reminder_id)
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return result
        except (IndexError, ValueError):
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": "❌ صيغة غير صحيحة. أرسل 'حذف <رقم>' مثل: حذف 1\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # Handle edit specific reminder
    if text.lower().startswith("تعديل "):
        try:
            reminder_id = int(text.split()[1])
            set_session(sender, {
                "menu": "reminder_edit_date",
                "last_menu": "reminder_main",
                "reminder_id": reminder_id
            })
            return {"reply": f"📅 أدخل تاريخ جديد للتذكير بالميلادي (أو 'تخطي' للاحتفاظ بالتاريخ الحالي):\nمثل: 17-08-2025\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        except (IndexError, ValueError):
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": "❌ صيغة غير صحيحة. أرسل 'تعديل <رقم>' مثل: تعديل 2\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # Main menu processing
    if current_menu == "main":
        if text == "2":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        elif text == "3":
            categories = get_categories()
            if not categories:
                return {"reply": "❌ لا توجد بيانات متاحة عن الصيدليات حاليًا.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
            reply = "💊 *قائمة الصيدليات:*\n\n"
            for category in categories:
                code, name, description, morning_start, morning_end, evening_start, evening_end = category
                reply += f"🏢 *{name}*\n{description}\n⏰ *دوام الصباح*: {morning_start} - {morning_end}\n⏰ *دوام المساء*: {evening_start} - {evening_end}\n\n"
            reply += "↩️ للرجوع (00) | 🏠 رئيسية (0)"
            set_session(sender, {"menu": "main", "last_menu": ""})
            return {"reply": reply}
        else:
            set_session(sender, {"menu": "main", "last_menu": ""})
            return {"reply": MAIN_MENU_TEXT}

    # Reminder main menu processing
    elif current_menu == "reminder_main":
        if text == "1":
            set_session(sender, {
                "menu": "reminder_date",
                "last_menu": "reminder_main",
                "reminder_type": "موعد",
                "interval_days": 0
            })
            return {"reply": f"📅 أرسل تاريخ الموعد بالميلادي فقط (مثل: 17-08-2025):\nسيتم تذكيرك قبل الموعد بيوم واحد.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        elif text == "2":
            set_session(sender, {
                "menu": "reminder_date",
                "last_menu": "reminder_main",
                "reminder_type": "يومي",
                "interval_days": 1
            })
            return {"reply": f"📅 أرسل تاريخ بدء التذكير اليومي بالميلادي (مثل: 17-08-2025):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        elif text == "3":
            set_session(sender, {
                "menu": "reminder_date",
                "last_menu": "reminder_main",
                "reminder_type": "أسبوعي",
                "interval_days": 7
            })
            return {"reply": f"📅 أرسل تاريخ بدء التذكير الأسبوعي بالميلادي (مثل: 17-08-2025):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        elif text == "4":
            return list_user_reminders(sender, sender)
        elif text == "5":
            return get_user_stats(sender, sender)
        else:
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": f"❌ اختر رقمًا من 1 إلى 5 أو أرسل 'حذف'.\n\n{REMINDER_MENU_TEXT}"}

    # Reminder date input processing
    elif current_menu == "reminder_date":
        date_info = is_valid_date(text)
        if date_info:
            formatted_date = f"{date_info['year']}-{date_info['month']:02d}-{date_info['day']:02d}"
            set_session(sender, {
                "menu": "reminder_time",
                "last_menu": "reminder_date",
                "reminder_type": session.get("reminder_type", "موعد"),
                "interval_days": session.get("interval_days", 0),
                "date": formatted_date
            })
            return {"reply": f"⏰ أدخل وقت التذكير بالصيغة HH:MM (مثل: 15:30):\n(يمكنك إرسال 'تخطي' لضبطه على 00:00)\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            set_session(sender, session)
            return {"reply": f"❌ صيغة التاريخ غير صحيحة. أرسل التاريخ مثل: 17-08-2025\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # Reminder time input processing
    elif current_menu == "reminder_time":
        time_info = is_valid_time(text) if text.lower() not in ["تخطي", "skip"] else {"hour": 0, "minute": 0}
        if time_info:
            formatted_time = f"{time_info['hour']:02d}:{time_info['minute']:02d}"
            set_session(sender, {
                "menu": "reminder_message",
                "last_menu": "reminder_time",
                "reminder_type": session.get("reminder_type", "موعد"),
                "interval_days": session.get("interval_days", 0),
                "date": session.get("date", ""),
                "time": formatted_time
            })
            return {"reply": f"📝 أدخل رسالة مخصصة للتذكير (أو 'تخطي' إذا لا تريد):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            set_session(sender, session)
            return {"reply": f"❌ صيغة الوقت غير صحيحة. أرسل الوقت مثل: 15:30 أو 'تخطي'\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # Reminder message input processing
    elif current_menu == "reminder_message":
        reminder_type = session.get("reminder_type", "موعد")
        interval_days = session.get("interval_days", 0)
        date_str = session.get("date", "")
        time_str = session.get("time", "00:00")
        
        # تحويل الوقت إلى UTC+3
        remind_at_dt = datetime.strptime(f"{date_str} {time_str}:00", "%Y-%m-%d %H:%M:%S")
        saudi_tz = pytz.timezone('Asia/Riyadh')  # UTC+3
        remind_at_dt = remind_at_dt.replace(tzinfo=pytz.utc).astimezone(saudi_tz)  # ضبط إلى UTC+3
        remind_at = remind_at_dt.strftime("%Y-%m-%d %H:%M:%S")  # حفظ كـ string
        
        if reminder_type == "موعد":
            remind_at_dt = remind_at_dt - timedelta(days=1)  # طرح يوم واحد
            remind_at = remind_at_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        message = None if text.lower() in ["تخطي", "skip"] else text
        if save_reminder(sender, reminder_type, message, remind_at, interval_days):
            repeat_text = f"يتكرر كل {interval_days} يوم" if interval_days > 0 else "لن يتكرر"
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": f"✅ تم ضبط التذكير بنجاح لـ '{reminder_type}' في {remind_at}\nالتكرار: {repeat_text}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": f"❌ حدث خطأ أثناء ضبط التذكير. حاول مرة أخرى.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # Edit reminder date input
    elif current_menu == "reminder_edit_date":
        reminder_id = session.get("reminder_id")
        if text.lower() in ["تخطي", "skip"]:
            set_session(sender, {
                "menu": "reminder_edit_time",
                "last_menu": "reminder_edit_date",
                "reminder_id": reminder_id
            })
            return {"reply": f"⏰ أدخل وقت التذكير الجديد بالصيغة HH:MM (مثل: 15:30) أو 'تخطي':\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        date_info = is_valid_date(text)
        if date_info:
            formatted_date = f"{date_info['year']}-{date_info['month']:02d}-{date_info['day']:02d}"
            set_session(sender, {
                "menu": "reminder_edit_time",
                "last_menu": "reminder_edit_date",
                "reminder_id": reminder_id,
                "new_date": formatted_date
            })
            return {"reply": f"⏰ أدخل وقت التذكير الجديد بالصيغة HH:MM (مثل: 15:30) أو 'تخطي':\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            set_session(sender, session)
            return {"reply": f"❌ صيغة التاريخ غير صحيحة. أرسل التاريخ مثل: 17-08-2025 أو 'تخطي'\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # Edit reminder time input
    elif current_menu == "reminder_edit_time":
        reminder_id = session.get("reminder_id")
        if text.lower() in ["تخطي", "skip"]:
            set_session(sender, {
                "menu": "reminder_edit_message",
                "last_menu": "reminder_edit_time",
                "reminder_id": reminder_id,
                "new_date": session.get("new_date", "")
            })
            return {"reply": f"📝 أدخل رسالة جديدة للتذكير (أو 'تخطي' للاحتفاظ بالرسالة الحالية):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        time_info = is_valid_time(text)
        if time_info:
            new_date = session.get("new_date", "")
            formatted_time = f"{time_info['hour']:02d}:{time_info['minute']:02d}"
            remind_at = f"{new_date} {formatted_time}:00" if new_date else None
            if new_date and remind_at and session.get("reminder_type", "") == "موعد":
                date_obj = datetime.strptime(new_date, "%Y-%m-%d")
                remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d") + f" {formatted_time}:00"
            set_session(sender, {
                "menu": "reminder_edit_message",
                "last_menu": "reminder_edit_time",
                "reminder_id": reminder_id,
                "new_remind_at": remind_at if remind_at else ""
            })
            return {"reply": f"📝 أدخل رسالة جديدة للتذكير (أو 'تخطي' للاحتفاظ بالرسالة الحالية):\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            set_session(sender, session)
            return {"reply": f"❌ صيغة الوقت غير صحيحة. أرسل الوقت مثل: 15:30 أو 'تخطي'\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # Edit reminder message input
    elif current_menu == "reminder_edit_message":
        reminder_id = session.get("reminder_id")
        new_remind_at = session.get("new_remind_at", "")
        message = None if text.lower() in ["تخطي", "skip"] else text
        result = update_reminder(sender, reminder_id, remind_at=new_remind_at if new_remind_at else None, message=message)
        set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
        return result

    # Fallback for unrecognized state or input
    set_session(sender, {"menu": "main", "last_menu": ""})
    return {"reply": MAIN_MENU_TEXT}
