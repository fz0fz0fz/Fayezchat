import os
import sqlite3
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
    "*أهلا بك في دليل خدمات القرين*\n"
    "يمكنك الإستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي🏢\n"
    "20- منبه📆"
)

def handle(msg: str, sender: str):
    text = msg.strip().lower()

    # رجوع للقائمة الرئيسية
    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    # رجوع للقائمة السابقة
    session = get_session(sender)
    if text == "00":
        if session in {"oil_change_duration", "istighfar_interval"}:
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

    # إيقاف التنبيهات
    if text == "توقف":
        conn = sqlite3.connect(REMINDERS_DB)
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        conn.commit()
        conn.close()
        set_session(sender, None)
        return {"reply": "🛑 تم إيقاف جميع التنبيهات بنجاح."}

    # عرض قائمة المنبه
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

    # في قائمة المنبه: اختيار النوع
    if session == "reminder_menu":
        if text == "1":
            set_session(sender, "oil_change_duration")
            return {"reply": (
                "🛢️ كم المدة لتغيير الزيت؟\n"
                "1 = شهر\n2 = شهرين\n3 = 3 أشهر\n\n"
                "↩️ للرجوع للقائمة السابقة: أرسل 00\n"
                "🏠 للقائمة الرئيسية: أرسل 0"
            )}
        if text == "3":
            set_session(sender, "istighfar_interval")
            return {"reply": (
                "🧎‍♂️ كم مرة تذكير استغفار؟\n"
                "1 = كل 30 دقيقة\n2 = كل ساعة\n3 = كل ساعتين\n\n"
                "↩️ للرجوع للقائمة السابقة: أرسل 00\n"
                "🏠 للقائمة الرئيسية: أرسل 0"
            )}
        return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

    # تذكير تغيير الزيت
    if session == "oil_change_duration":
        if text in {"1", "2", "3"}:
            months = int(text)
            at = datetime.now() + timedelta(days=30 * months)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender,type,remind_at) VALUES (?,?,?)",
                (sender, "تغيير الزيت", at.strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            conn.close()
            set_session(sender, None)
            return {"reply": f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."}
        return {"reply": "📌 1، 2 أو 3."}

    # تذكير استغفار دوري
    if session == "istighfar_interval":
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
            conn.commit()
            conn.close()
            set_session(sender, None)
            return {"reply": f"✅ تم ضبط تذكير استغفار كل {mins} دقيقة."}
        return {"reply": "📌 1، 2 أو 3."}

    return {"reply": "🤖 أرسل 'منبه' لعرض القائمة أو 'توقف' لإلغاء التنبيهات."}
