import os
import sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session
import re

REMINDERS_DB = os.getenv("REMINDERS_DB_PATH", "reminders.db")

def init_reminder_db():
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            type TEXT NOT NULL,
            interval_minutes INTEGER,
            remind_at TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

MAIN_MENU_TEXT = (
    "*أهلاً بك في دليل خدمات القرين*\n"
    "يمكنك الاستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي 🏢\n"
    "20- منبّه 📆"
)

REMINDER_MENU_TEXT = (
    "⏰ *منبّه*\n"
    "اختر نوع التذكير الذي تريده:\n\n"
    "2️⃣ موعد مستشفى أو مناسبة\n"
    "6️⃣ تنبيهاتي الحالية\n\n"
    "❌ لحذف جميع التنبيهات أرسل: حذف\n"
    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
)

def save_reminder(sender, type_, interval, remind_at):
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute("INSERT INTO reminders (sender, type, interval_minutes, remind_at) VALUES (?, ?, ?, ?)",
              (sender, type_, interval, remind_at))
    conn.commit()
    conn.close()

def list_user_reminders(sender):
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute("SELECT type, remind_at FROM reminders WHERE sender = ? AND active = 1", (sender,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return {"reply": "📭 لا توجد أي تنبيهات حالياً.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    reply = "*📋 قائمة تنبيهاتك:*\n"
    for idx, (type_, remind_at) in enumerate(rows, 1):
        reply += f"{idx}- نوع: {type_} | التاريخ: {remind_at}\n"
    reply += "\n❌ لحذف جميع التنبيهات أرسل: حذف\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
    return {"reply": reply}

def delete_all_reminders(sender):
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
    conn.commit()
    conn.close()
    return {"reply": "✅ تم حذف جميع التنبيهات بنجاح.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

def handle(msg: str, sender: str) -> dict:
    session = get_session(sender)
    text = msg.strip()

    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    if text == "00":
        if session and "last_menu" in session:
            set_session(sender, {"menu": session["last_menu"]})
            return handle(session["last_menu"], sender)
        else:
            return {"reply": MAIN_MENU_TEXT}

    if text == "حذف":
        return delete_all_reminders(sender)

    if session is None:
        if text == "20":
            set_session(sender, {"menu": "reminder_main"})
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
                remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d 09:00:00")
                save_reminder(sender, "موعد", None, remind_at)
                set_session(sender, {"menu": "reminder_main"})
                return {
                    "reply": f"✅ تم ضبط التذكير، سيتم التذكير بتاريخ {remind_at.split()[0]}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
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
