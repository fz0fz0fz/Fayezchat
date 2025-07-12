import re
import sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session

DB_PATH = "reminders.db"

# ============ إنشاء الجدول إن لم يكن موجودًا ============
def init_reminder_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT,
            message TEXT,
            remind_at DATE
        )
    ''')
    conn.commit()
    conn.close()

# ============ حفظ تذكير جديد ============
def save_reminder(user_id, reminder_type, message, remind_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reminders (user_id, type, message, remind_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, reminder_type, message, remind_at))
    conn.commit()
    conn.close()

# ============ حذف جميع التذكيرات ============
def delete_all_reminders(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return {"reply": "✅ تم حذف جميع التذكيرات الخاصة بك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

# ============ عرض تذكيرات المستخدم ============
def list_user_reminders(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, type, remind_at FROM reminders WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"reply": "📭 لا توجد أي تنبيهات حالياً.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    reply = "🔔 تنبيهاتك الحالية:\n\n"
    for row in rows:
        reply += f"- {row[1]} بتاريخ {row[2]}\n"
    reply += "\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
    return {"reply": reply}

# ============ القوائم ============
REMINDER_MENU_TEXT = (
    "⏰ *منبه*\n\n"
    "اختر نوع التذكير الذي تريده:\n\n"
    "2️⃣ موعد مستشفى أو مناسبة\n"
    "6️⃣ تنبيهاتي الحالية\n\n"
    "❌ لحذف جميع التنبيهات أرسل: حذف\n"
    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
)

MAIN_MENU_TEXT = (
    "*أهلاً بك في دليل خدمات القرين*\n"
    "يمكنك الاستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي🏢\n"
    "20- منبه 📆"
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

    if text == "حذف":
        return delete_all_reminders(sender)

    if session is None:
        if text == "20":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        else:
            return {"reply": MAIN_MENU_TEXT}

    if session.get("menu") == "reminder_main":
        if text == "2":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main"})
            return {
                "reply": (
                    "📅 أرسل تاريخ الموعد بالميلادي فقط :\n"
                    "مثل: 17-08-2025\n"
                    "وسيتم تذكيرك قبل الموعد بيوم واحد\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "6":
            return list_user_reminders(sender)
        else:
            return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

    if session.get("menu") == "reminder_date":
        try:
            parts = [int(p) for p in re.split(r"[-./_\\\s]+", text.strip()) if p]
            if len(parts) == 3:
                day, month, year = parts
                if year < 100: year += 2000
                date_obj = datetime(year, month, day)
                remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                save_reminder(sender, "موعد", None, remind_at)
                set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
                return {
                    "reply": f"✅ تم ضبط التذكير، سيتم التذكير بتاريخ {remind_at}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
                }
            else:
                raise ValueError
        except:
            return {
                "reply": (
                    "❗️صيغة غير صحيحة. أرسل التاريخ مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }

    return {"reply": MAIN_MENU_TEXT}
