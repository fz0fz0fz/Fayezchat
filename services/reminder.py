import sqlite3
from datetime import datetime, timedelta

DB_PATH = "reminders.db"  # ✅ حفظ القاعدة في مجلد المشروع لتفادي مشاكل /mnt/data

# إنشاء جدول التذكيرات إذا لم يكن موجودًا
def init_reminder_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            type TEXT NOT NULL,
            value TEXT,
            remind_at TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_reminder_db()

def handle(msg, sender):
    msg = msg.strip().lower()

    if msg in ["20", "٢٠", "منبه", "منبّه", "تذكير"]:
        return """*🔔 خدمة المنبه - اختر ما تود التذكير به:*

1️⃣ تغيير الزيت  
2️⃣ موعد مستشفى أو مناسبة  
3️⃣ تذكير استغفار  
4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة  
5️⃣ تذكير بأخذ الدواء  

🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة."""

    # تغيير الزيت - تحديد المدة
    if msg == "1":
        return "كم المدة التي ترغب أن نذكرك بعدها لتغيير الزيت؟\n\n1- شهر\n2- شهرين\n3- 3 أشهر\n\nمثال: أرسل 1-1 أو 1-2 أو 1-3"

    # تغيير الزيت - إدخال المدة المحددة
    if msg in ["1-1", "1-2", "1-3"]:
        months = {"1-1": 1, "1-2": 2, "1-3": 3}[msg]
        remind_at = datetime.now() + timedelta(days=30 * months)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO reminders (sender, type, remind_at) VALUES (?, ?, ?)",
                  (sender, "تغيير الزيت", remind_at.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        return f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."

    # أمر الإيقاف
    if msg == "توقف":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        conn.commit()
        conn.close()
        return "🛑 تم إيقاف جميع التنبيهات بنجاح."

    return "🤖 يرجى اختيار خيار صحيح من خدمة المنبه أو إرسال 'توقف' لإيقاف التنبيهات."
