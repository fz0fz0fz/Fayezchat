# services/reminder.py
import os
import re
import sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session


# -------------------------------------------------
DB_PATH = "reminders.db"
# -------------------------------------------------


# ============ إنشاء الجدول (مع طباعة حالة الإنشاء) ============
def init_reminder_db() -> None:
    """يتأكد من وجود reminders.db ويُنشئ الجدول عند الحاجة"""
    if not os.path.exists(DB_PATH):
        print("📁 يتم إنشاء قاعدة البيانات reminders.db لأول مرة…")
    else:
        print("✅ قاعدة البيانات reminders.db موجودة بالفعل.")

    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   TEXT NOT NULL,
            type      TEXT,
            message   TEXT,
            remind_at DATE
        )
        """
    )
    conn.commit()
    conn.close()


# ============ CRUD helper functions ============
def save_reminder(user_id, reminder_type, message, remind_at):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (user_id, type, message, remind_at) VALUES (?,?,?,?)",
        (user_id, reminder_type, message, remind_at),
    )
    conn.commit(); conn.close()


def delete_all_reminders(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
    conn.commit(); conn.close()
    return {"reply": "✅ تم حذف جميع التذكيرات الخاصة بك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}


def list_user_reminders(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT id, type, remind_at FROM reminders WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"reply": "📭 لا توجد أي تنبيهات حالياً.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    reply = "🔔 تنبيهاتك الحالية:\n\n"
    for _id, r_type, at in rows:
        reply += f"- {r_type} بتاريخ {at}\n"
    reply += "\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
    return {"reply": reply}


# ============ نصوص القوائم ============
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


# ============ المعالج الرئيسي ============
def handle(msg: str, sender: str) -> dict:
    session = get_session(sender)
    text    = msg.strip()

    # --- أوامر عامة ---
    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    if text == "00":
        if session and "last_menu" in session:
            last_menu = session["last_menu"]
            set_session(sender, {"menu": last_menu, "last_menu": "main"})
            return handle(last_menu, sender)
        return {"reply": MAIN_MENU_TEXT}

    if text == "حذف":
        return delete_all_reminders(sender)

    # --- دخول خدمة المنبّه ---
    if session is None:
        if text == "20":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        return {"reply": MAIN_MENU_TEXT}

    # --- قائمة المنبّه الرئيسية ---
    if session.get("menu") == "reminder_main":
        if text == "2":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main"})
            return {
                "reply": (
                    "📅 أرسل تاريخ الموعد بالميلادي فقط:\n"
                    "مثل: 17-08-2025\n"
                    "وسيتم تذكيرك قبل الموعد بيوم واحد\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        if text == "6":
            return list_user_reminders(sender)
        return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

    # --- إدخال تاريخ الموعد ---
    if session.get("menu") == "reminder_date":
        try:
            parts = [int(p) for p in re.split(r"[-./_\\\s]+", text) if p]
            if len(parts) != 3:
                raise ValueError
            day, month, year = parts
            if year < 100:
                year += 2000
            date_obj  = datetime(year, month, day)
            remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
            save_reminder(sender, "موعد", None, remind_at)

            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {
                "reply": f"✅ تم ضبط التذكير، سيتم التذكير بتاريخ {remind_at}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
            }
        except Exception:
            return {
                "reply": (
                    "❗️ صيغة غير صحيحة. أرسل التاريخ مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }

    # افتراضي
    return {"reply": MAIN_MENU_TEXT}
