import sqlite3
from datetime import datetime, timedelta
from typing import Optional

REMINDERS_DB = "reminders.db"
SESSIONS_DB = "sessions.db"

# ================ قاعدة بيانات التذكيرات =================

def init_reminders_db() -> None:
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            type TEXT NOT NULL,
            value TEXT,
            remind_at TEXT,
            interval_minutes INTEGER,
            active INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()
    conn.close()

# ================ قاعدة بيانات الجلسات =================

def init_sessions_db() -> None:
    conn = sqlite3.connect(SESSIONS_DB)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            sender TEXT PRIMARY KEY,
            current_state TEXT
        )
        """
    )
    conn.commit()
    conn.close()

init_reminders_db()
init_sessions_db()

# --------- أدوات الجلسات ---------

def set_session(sender: str, state: Optional[str]) -> None:
    conn = sqlite3.connect(SESSIONS_DB)
    c = conn.cursor()
    if state:
        c.execute(
            "REPLACE INTO sessions (sender, current_state) VALUES (?, ?)",
            (sender, state),
        )
    else:
        c.execute("DELETE FROM sessions WHERE sender = ?", (sender,))
    conn.commit()
    conn.close()

def get_session(sender: str) -> Optional[str]:
    conn = sqlite3.connect(SESSIONS_DB)
    c = conn.cursor()
    c.execute("SELECT current_state FROM sessions WHERE sender = ?", (sender,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ----------- الدالة الرئيسية ------------

def handle(msg: str, sender: str) -> str:
    text = msg.strip().lower()

    # --------------- إيقاف جميع التنبيهات ---------------
    if text == "توقف":
        conn = sqlite3.connect(REMINDERS_DB)
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        conn.commit()
        conn.close()
        set_session(sender, None)
        return "🛑 تم إيقاف جميع التنبيهات بنجاح."

    session_state = get_session(sender)

    # ====== الخطوة ❶ : قائمة المنبه ======
    if text in {"20", "٢٠", "منبه", "منبّه", "تذكير"}:
        set_session(sender, "reminder_menu")
        return (
            "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
            "1️⃣ تغيير الزيت\n"
            "2️⃣ موعد مستشفى أو مناسبة\n"
            "3️⃣ تذكير استغفار\n"
            "4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة\n"
            "5️⃣ تذكير بأخذ الدواء\n\n"
            "🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة."
        )

    # ====== الخطوة ❷ : اختيار نوع
