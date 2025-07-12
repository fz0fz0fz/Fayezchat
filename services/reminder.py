import sqlite3 import os import re from datetime import datetime, timedelta from services.session import get_session, set_session

DB_PATH = os.path.join(os.path.dirname(file), "reminders.db")

───────────────────────────────────────────

تهيئة قاعدة البيانات وإنشاء الجدول إن لزم

───────────────────────────────────────────

def init_reminder_db(): conn = sqlite3.connect(DB_PATH) c = conn.cursor() c.execute(''' CREATE TABLE IF NOT EXISTS reminders ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, type TEXT, message TEXT, remind_at TEXT ) ''') conn.commit() conn.close()

───────────────────────────────────────────

حفظ تذكير جديد في قاعدة البيانات

───────────────────────────────────────────

def save_reminder(user_id, type_, message, remind_at): conn = sqlite3.connect(DB_PATH) c = conn.cursor() c.execute('''INSERT INTO reminders (user_id, type, message, remind_at) VALUES (?, ?, ?, ?)''', (user_id, type_, message, remind_at)) conn.commit() conn.close()

───────────────────────────────────────────

استرجاع التذكيرات الحالية للمستخدم

───────────────────────────────────────────

def list_user_reminders(user_id): conn = sqlite3.connect(DB_PATH) c = conn.cursor() c.execute('''SELECT remind_at FROM reminders WHERE user_id = ? ORDER BY remind_at''', (user_id,)) rows = c.fetchall() conn.close()

if not rows:
    return {"reply": "📪 لا توجد أي تنبيهات حالياً.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

reply = "📋 تنبيهاتك الحالية:\n\n"
for i, row in enumerate(rows, 1):
    reply += f"{i}- {row[0]}\n"

reply += "\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
return {"reply": reply}

───────────────────────────────────────────

حذف كل التنبيهات لمستخدم معين

───────────────────────────────────────────

def delete_all_reminders(user_id): conn = sqlite3.connect(DB_PATH) c = conn.cursor() c.execute('''DELETE FROM reminders WHERE user_id = ?''', (user_id,)) conn.commit() conn.close() return {"reply": "🗑️ تم حذف جميع التنبيهات بنجاح.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

───────────────────────────────────────────

نص القائمة الرئيسية

───────────────────────────────────────────

MAIN_MENU_TEXT = """أهلاً بك في دليل خدمات القرين يمكنك الاستعلام عن الخدمات التالية:

1️⃣ حكومي🏢 20- ⏰ منبه"""

REMINDER_MENU_TEXT = ( "⏰ منبه\n" "اختر نوع التذكير الذي تريده:\n\n" "2️⃣ موعد مستشفى أو مناسبة\n" "6️⃣ تنبيهاتي الحالية\n\n" "❌ لحذف جميع التنبيهات أرسل: حذف\n" "↩️ للرجوع (00) | 🏠 رئيسية (0)" )

───────────────────────────────────────────

دالة المعالجة الرئيسية

───────────────────────────────────────────

def handle(msg: str, sender: str) -> dict: session = get_session(sender) text = msg.strip()

if text == "0":
    set_session(sender, None)
    return {"reply": MAIN_MENU_TEXT}

if text == "00":
    if session and "last_menu" in session:
        last_menu = session["last_menu"]
        set_session(sender, {"menu": last_menu, "last_menu": "main"})
        if last_menu == "reminder_main":
            return {"reply": REMINDER_MENU_TEXT}
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
        parts = [int(p) for p in re.split(r"[-./_\\\\s]+", text.strip()) if p]
        if len(parts) == 3:
            day, month, year = parts
            if year < 100: year += 2000
            date_obj = datetime(year, month, day)
            remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
            save_reminder(sender, "hospital", None, remind_at)
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

