# services/reminder.py
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# مسار ملف قاعدة البيانات
DB_PATH = "/mnt/data/reminders.db"

# إنشاء جدول التذكيرات إذا لم يكن موجودًا
def init_reminder_db() -> None:
    Path("/mnt/data").mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender    TEXT    NOT NULL,
            type      TEXT    NOT NULL,
            value     TEXT,
            remind_at TEXT,
            active    INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()
    conn.close()


init_reminder_db()

# ============ دالة المعالجة الرئيسية ============ #
def handle(msg: str, sender: str) -> str:
    """
    تُعالج جميع رسائل خدمة المنبه، وتُنشئ التذكيرات في قاعدة البيانات.
    """
    text = msg.strip().lower()

    # القائمة الرئيسـية للمنبه
    if text in {"20", "منبه", "منبّه", "تذكير"}:
        return (
            "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
            "1️⃣ تغيير الزيت\n"
            "2️⃣ موعد مستشفى أو مناسبة\n"
            "3️⃣ تذكير استغفار\n"
            "4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة\n"
            "5️⃣ تذكير بأخذ الدواء\n\n"
            "🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة."
        )

    # ------------------------------------------------
    # 1️⃣ تغيير الزيت
    # ------------------------------------------------
    if text == "1":
        return (
            "🛢️ *كم المدة التي ترغب أن نذكرك بعدها لتغيير الزيت؟*\n\n"
            "1- شهر\n"
            "2- شهرين\n"
            "3- 3 أشهر"
        )

    if text in {"1-1", "1-2", "1-3"}:
        months = {"1-1": 1, "1-2": 2, "1-3": 3}[text]
        remind_at = datetime.now() + timedelta(days=30 * months)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO reminders (sender, type, value, remind_at) VALUES (?,?,?,?)",
            (sender, "تغيير الزيت", f"{months}_months", remind_at.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()

        return f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."

    # ------------------------------------------------
    # إيقاف جميع التنبيهات
    # ------------------------------------------------
    if text == "توقف":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        conn.commit()
        conn.close()
        return "🛑 تم إيقاف جميع التنبيهات بنجاح."

    # ------------------------------------------------
    # في حال إدخال غير مفهوم
    # ------------------------------------------------
    return (
        "🤖 لم أفهم طلبك داخل خدمة المنبه.\n"
        "🔙 أرسل 'منبه' لعرض القائمة، أو 'توقف' لإلغاء التنبيهات."
    )
