import os
import sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session

# ------------------------------------------------------------
# ثوابت المسار ونص القائمة الرئيسية
# ------------------------------------------------------------

REMINDERS_DB = os.getenv("REMINDERS_DB_PATH", "reminders.db")

def init_reminder_db():
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            type  TEXT NOT NULL,
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
