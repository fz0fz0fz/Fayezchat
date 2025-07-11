"""خدمة المنبّه: تغيير الزيت + تذكير الاستغفار المتكرر"""

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

# --------- أدوات جلسات ---------

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

    # احصل على حالة الجلسة إن وجدت
    session_state = get_session(sender)

    # --------------- متابعة خطوات تغيير الزيت ---------------
    if session_state == "oil_change_waiting_duration":
        if text in {"1", "2", "3"}:
            months = int(text)
            remind_at = datetime.now() + timedelta(days=30 * months)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender, type, remind_at) VALUES (?,?,?)",
                (sender, "تغيير الزيت", remind_at.strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            set_session(sender, None)
            return f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."
        return "📌 اختر 1 = شهر، 2 = شهرين، 3 = 3 أشهر."

    # --------------- متابعة خطوات الاستغفار ---------------
    if session_state == "istighfar_waiting_interval":
        interval_map = {"1": 30, "2": 60, "3": 120}
        if text in interval_map:
            minutes = interval_map[text]
            next_time = datetime.now() + timedelta(minutes=minutes)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender, type, interval_minutes, remind_at) VALUES (?,?,?,?)",
                (sender, "استغفار", minutes, next_time.strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            set_session(sender, None)
            return f"✅ تم ضبط تذكير الاستغفار كل {minutes} دقيقة."
        return "📌 اختر: 1 = كل 30 دقيقة، 2 = كل ساعة، 3 = كل ساعتين."

    # --------------- القائمة الرئيسية للمنبه ---------------
    if text in {"20", "٢٠", "منبه", "منبّه", "تذكير"}:
        return (
            "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
            "1️⃣ تغيير الزيت\n"
            "2️⃣ موعد مستشفى أو مناسبة\n"
            "3️⃣ تذكير استغفار\n"
            "4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة\n"
            "5️⃣ تذكير بأخذ الدواء\n\n"
            "🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة."
        )

    # --------------- خيار تغيير الزيت ---------------
    if text == "1":
        set_session(sender, "oil_change_waiting_duration")
        return (
            "🛢️ *كم المدة التي ترغب أن نذكرك بعدها لتغيير الزيت؟*\n\n"
            "1️⃣ شهر\n"
            "2️⃣ شهرين\n"
            "3️⃣ 3 أشهر"
        )

    # --------------- خيار الاستغفار ---------------
    if text == "3":
        set_session(sender, "istighfar_waiting_interval")
        return (
            "🧎‍♂️ *كم مرة ترغب بالتذكير بالاستغفار؟*\n\n"
            "1️⃣ كل نصف ساعة\n"
            "2️⃣ كل ساعة\n"
            "3️⃣ كل ساعتين"
        )

    # --------------- في حال طلب غير مفهوم ---------------
    return "🤖 لم أفهم طلبك في خدمة المنبه. أرسل 'منبه' لعرض القائمة أو 'توقف' لإلغاء التنبيهات."
