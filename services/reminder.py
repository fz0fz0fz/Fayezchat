# services/reminder.py
import os
import sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session

REMINDERS_DB = os.getenv("REMINDERS_DB_PATH", "reminders.db")

def init_reminder_db():
    """إنشاء جدول التذكيرات إذا لم يكن موجودًا."""
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            type   TEXT NOT NULL,
            interval_minutes INTEGER,
            remind_at TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()
    conn.close()

# استدعاء التهيئة مرة واحدة عند استيراد الملف
init_reminder_db()

# نصّ القائمة الرئيسية المختصر
MAIN_MENU_TEXT = (
    "*أهلاً بك في دليل خدمات القرين*\n"
    "1️⃣ حكومي🏢\n"
    "20- منبه📆"
)

def handle(msg: str, sender: str):
    text = msg.strip().lower()

    # ——— 0 : الرجوع للقائمة الرئيسية ———
    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    # ——— توقــف : إيقاف كل التنبيهات ———
    if text == "توقف":
        with sqlite3.connect(REMINDERS_DB) as conn:
            conn.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        set_session(sender, None)
        return {"reply": "🛑 تم إيقاف جميع التنبيهات بنجاح."}

    # جلسة المستخدم الحالية (إن وُجدت)
    session = get_session(sender)

    # ——— فتح قائمة المنبّه ———
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
            "0️⃣ للرجوع إلى القائمة الرئيسية."
        )}

    # ——— داخل قائمة المنبّه ———
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
                "📅 أرسل تاريخ الموعد بصيغة *YYYY-MM-DD* (ميلادي).\n"
                "مثال: 2025-08-17\n\n"
                "↩️ للرجوع (00) | 🏠 رئيسية (0)"
            )}
        if text == "3":
            set_session(sender, "istighfar_interval")
            return {"reply": (
                "🧎‍♂️ كم مرة تذكير استغفار؟\n"
                "1 = كل 30 دقيقة\n2 = كل ساعة\n3 = كل ساعتين"
            )}
        return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

    # ——— ❶ تغيير الزيت ———
    if session == "oil_change_duration":
        if text == "00":
            set_session(sender, "reminder_menu")
            return handle("20", sender)
        if text in {"1", "2", "3"}:
            months = int(text)
            remind_at = datetime.now() + timedelta(days=30 * months)
            with sqlite3.connect(REMINDERS_DB) as conn:
                conn.execute(
                    "INSERT INTO reminders (sender, type, remind_at) VALUES (?, ?, ?)",
                    (sender, "تغيير الزيت", remind_at.strftime("%Y-%m-%d %H:%M:%S"))
                )
            set_session(sender, None)
            return {"reply": f"✅ تم الضبط بعد {months} شهر."}
        return {"reply": "📌 اختر 1 أو 2 أو 3."}

    # ——— ❷ موعد مستشفى أو مناسبة ———
    if session == "appointment_date":
        if text == "00":
            set_session(sender, "reminder_menu")
            return handle("20", sender)
        try:
            date_obj = datetime.strptime(text, "%Y-%m-%d")
            remind_at = date_obj - timedelta(days=1)   # قبل بيوم
            with sqlite3.connect(REMINDERS_DB) as conn:
                conn.execute(
                    "INSERT INTO reminders (sender, type, remind_at) VALUES (?, ?, ?)",
                    (sender, "موعد", remind_at.strftime("%Y-%m-%d %H:%M:%S"))
                )
            set_session(sender, None)
            return {"reply": f"📌 تم ضبط التذكير، سيتم تذكيرك يوم {remind_at.date()}."}
        except ValueError:
            return {"reply": "❌ صيغة التاريخ خطأ. استخدم YYYY-MM-DD (مثل 2025-08-17)."}

    # ——— ❸ استغفار دوري ———
    if session == "istighfar_interval":
        if text == "00":
            set_session(sender, "reminder_menu")
            return handle("20", sender)
        map_i = {"1": 30, "2": 60, "3": 120}
        if text in map_i:
            mins = map_i[text]
            remind_at = datetime.now() + timedelta(minutes=mins)
            with sqlite3.connect(REMINDERS_DB) as conn:
                conn.execute(
                    "INSERT INTO reminders (sender, type, interval_minutes, remind_at) "
                    "VALUES (?, ?, ?, ?)",
                    (sender, "استغفار", mins, remind_at.strftime("%Y-%m-%d %H:%M:%S"))
                )
            set_session(sender, None)
            return {"reply": f"✅ تم ضبط تذكير استغفار كل {mins} دقيقة."}
        return {"reply": "📌 اختر 1 أو 2 أو 3."}

    # ——— افتراضي ———
    return {"reply": "🤖 أرسل 'منبه' لعرض القائمة أو 'توقف' لإلغاء التنبيهات."}
