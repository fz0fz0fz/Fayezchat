# services/reminder.py
import re
import sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session

DB_PATH = "reminders.db"

# ============ إنشاء الجدول إن لم يكن موجودًا ============
def init_reminder_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                message TEXT,
                remind_at TEXT NOT NULL,
                interval_days INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        print("✅ تم إنشاء قاعدة البيانات reminders.db إن لم تكن موجودة.")
    except Exception as e:
        print(f"❌ خطأ أثناء إنشاء قاعدة البيانات: {e}")
    finally:
        conn.close()

# ============ حفظ تذكير جديد ============
def save_reminder(user_id, reminder_type, message, remind_at, interval_days=0):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, type, message, remind_at, interval_days, active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (user_id, reminder_type, message, remind_at, interval_days))
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ أثناء حفظ التذكير: {e}")
    finally:
        conn.close()

# ============ حذف جميع التذكيرات ============
def delete_all_reminders(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE user_id = ?', (user_id,))
        conn.commit()
        return {"reply": "✅ تم حذف جميع التذكيرات الخاصة بك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    except Exception as e:
        return {"reply": f"❌ خطأ أثناء حذف التذكيرات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        conn.close()

# ============ عرض تذكيرات المستخدم ============
def list_user_reminders(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, type, remind_at, interval_days FROM reminders WHERE user_id = ? AND active = 1', (user_id,))
        rows = cursor.fetchall()

        if not rows:
            return {"reply": "📭 لا توجد أي تنبيهات نشطة حاليًا.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

        reply = "🔔 تنبيهاتك النشطة الحالية:\n\n"
        for row in rows:
            interval_text = f" (يتكرر كل {row[3]} يوم)" if row[3] > 0 else ""
            reply += f"- {row[1]}{interval_text} بتاريخ {row[2]}\n"
        reply += "\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"❌ خطأ أثناء عرض التذكيرات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        conn.close()

# ============ القوائم ============
REMINDER_MENU_TEXT = (
    "⏰ *منبه*\n\n"
    "اختر نوع التذكير الذي تريده:\n\n"
    "1️⃣ موعد مستشفى أو مناسبة\n"
    "2️⃣ تذكير يومي\n"
    "3️⃣ تذكير أسبوعي\n"
    "4️⃣ تنبيهاتي الحالية\n\n"
    "❌ لحذف جميع التنبيهات أرسل: حذف\n"
    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
)

MAIN_MENU_TEXT = (
    "*أهلاً بك في دليل خدمات القرين*\n"
    "يمكنك الاستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي🏢\n"
    "2️⃣ منبه 📆"
)

# ============ المعالجة الرئيسية ============
def handle(msg: str, sender: str) -> dict:
    session = get_session(sender)
    text = msg.strip()

    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    if text == "00":
        if session and "last_menu" in session:
            last_menu = session["last_menu"]
            set_session(sender, {"menu": last_menu, "last_menu": "main"})
            return handle(last_menu, sender)
        else:
            return {"reply": MAIN_MENU_TEXT}

    if text.lower() == "حذف":
        return delete_all_reminders(sender)

    if session is None:
        if text == "2":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        else:
            return {"reply": MAIN_MENU_TEXT}

    if session.get("menu") == "reminder_main":
        if text == "1":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main", "reminder_type": "موعد", "interval_days": 0})
            return {
                "reply": (
                    "📅 أرسل تاريخ الموعد بالميلادي فقط:\n"
                    "مثل: 17-08-2025\n"
                    "وسيتم تذكيرك قبل الموعد بيوم واحد\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "2":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main", "reminder_type": "يومي", "interval_days": 1})
            return {
                "reply": (
                    "📅 أرسل تاريخ بدء التذكير اليومي بالميلادي:\n"
                    "مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "3":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main", "reminder_type": "أسبوعي", "interval_days": 7})
            return {
                "reply": (
                    "📅 أرسل تاريخ بدء التذكير الأسبوعي بالميلادي:\n"
                    "مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "4":
            return list_user_reminders(sender)
        else:
            return {"reply": "↩️ اختر رقم صحيح أو أرسل 'حذف' لإزالة جميع التنبيهات."}

    if session.get("menu") == "reminder_date":
        try:
            parts = [int(p) for p in re.split(r"[-./_\\\s]+", text.strip()) if p]
            if len(parts) == 3:
                day, month, year = parts
                if year < 100: year += 2000
                date_obj = datetime(year, month, day)
                reminder_type = session.get("reminder_type", "موعد")
                interval_days = session.get("interval_days", 0)
                
                remind_at = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                if reminder_type == "موعد":
                    remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                
                save_reminder(sender, reminder_type, None, remind_at, interval_days)
                set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
                repeat_text = f"يتكرر كل {interval_days} يوم" if interval_days > 0 else "لن يتكرر"
                return {
                    "reply": f"✅ تم ضبط التذكير بنجاح لـ '{reminder_type}' بتاريخ {remind_at}\n"
                             f"التكرار: {repeat_text}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
                }
            else:
                raise ValueError
        except Exception as e:
            return {
                "reply": (
                    "❗️ صيغة غير صحيحة. أرسل التاريخ مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }

    return {"reply": MAIN_MENU_TEXT}
