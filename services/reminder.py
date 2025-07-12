import os
import sqlite3
import re
from datetime import datetime, timedelta
from services.session import get_session, set_session

REMINDERS_DB = os.getenv("REMINDERS_DB_PATH", "reminders.db")

def init_reminder_db():
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            type TEXT NOT NULL,
            interval_minutes INTEGER,
            remind_at TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

MAIN_MENU_TEXT = (
    "أهلا بك في دليل خدمات القرين\n"
    "يمكنك الإستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي🏢\n"
    "20- منبه📆"
)

def handle(msg: str, sender: str):
    text = msg.strip().lower()
    session = get_session(sender)

    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    if text == "توقف":
        conn = sqlite3.connect(REMINDERS_DB)
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        conn.commit()
        conn.close()
        set_session(sender, None)
        return {"reply": "🛑 تم إيقاف جميع التنبيهات بنجاح."}

    if text in {"20", "٢٠", "منبه", "تذكير", "منبّه"}:
        set_session(sender, "reminder_menu")
        return {"reply": (
            "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
            "1️⃣ تغيير الزيت\n"
            "2️⃣ موعد مستشفى أو مناسبة\n"
            "3️⃣ تذكير استغفار\n"
            "4️⃣ تذكير صلاة الجمعة\n"
            "5️⃣ تذكير الدواء\n\n"
            "🛑 أرسل 'توقف' لإيقاف أي تنبيهات.\n"
            "0️⃣ للرجوع للقائمة الرئيسية."
        )}

    if session == "reminder_menu":
        if text == "1":
            set_session(sender, "oil_change_duration")
            return {"reply": (
                "🛢️ كم المدة لتغيير الزيت؟\n"
                "1 = شهر\n2 = شهرين\n3 = 3 أشهر\n\n"
                "↩️ للرجوع (00) | 🏠 رئيسية (0)"
            )}
        if text == "2":
            set_session(sender, "appointment_date")
            return {"reply": (
                "📅 أرسل تاريخ الموعد بصيغة:\n"
                "اليوم-الشهر-السنة مثل: 17-08-2025 أو 17/8/2025\n\n"
                "↩️ للرجوع (00) | 🏠 رئيسية (0)"
            )}
        if text == "3":
            set_session(sender, "istighfar_interval")
            return {"reply": (
                "🧎‍♂️ كم مرة تذكير استغفار؟\n"
                "1 = كل 30 دقيقة\n2 = كل ساعة\n3 = كل ساعتين"
            )}
        return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

    if session == "oil_change_duration":
        if text == "00":
            set_session(sender, "reminder_menu")
            return handle("20", sender)
        if text in {"1", "2", "3"}:
            months = int(text)
            at = datetime.now() + timedelta(days=30 * months)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender,type,remind_at) VALUES (?,?,?)",
                (sender, "تغيير الزيت", at.strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit(); conn.close()
            set_session(sender, None)
            return {"reply": f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."}
        return {"reply": "📌 1، 2 أو 3."}

    if session == "appointment_date":
        if text == "00":
            set_session(sender, "reminder_menu")
            return handle("20", sender)
        try:
            # دعم تنسيقات مختلفة للتاريخ
            pattern = r"(\d{1,2})[- /.\\_](\d{1,2})[- /.\\_](\d{4})"
            match = re.match(pattern, text)
            if not match:
                raise ValueError("Invalid format")

            day, month, year = map(int, match.groups())
            date = datetime(year, month, day)
            remind_at = date - timedelta(days=1)

            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender, type, remind_at) VALUES (?, ?, ?)",
                (sender, "موعد مستشفى أو مناسبة", remind_at.strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit(); conn.close()
            set_session(sender, None)
            return {"reply": f"📌 تم ضبط التذكير، سيتم تذكيرك يوم {remind_at.date()} بإذن الله."}
        except:
            return {"reply": "❌ صيغة التاريخ غير صحيحة. مثال: 17-08-2025 أو 17/8/2025"}

    if session == "istighfar_interval":
        if text == "00":
            set_session(sender, "reminder_menu")
            return handle("20", sender)
        map_i = {"1":30,"2":60,"3":120}
        if text in map_i:
            mins = map_i[text]
            at = datetime.now() + timedelta(minutes=mins)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender,type,interval_minutes,remind_at) VALUES (?,?,?,?)",
                (sender, "استغفار", mins, at.strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit(); conn.close()
            set_session(sender, None)
            return {"reply": f"✅ تم ضبط تذكير استغفار كل {mins} دقيقة."}
        return {"reply": "📌 1، 2 أو 3."}

    return {"reply": "🤖 أرسل 'منبه' لعرض القائمة أو 'توقف' لإلغاء التنبيهات."}
