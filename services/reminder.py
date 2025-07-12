import sqlite3 from datetime import datetime, timedelta from services.session import get_session, set_session

REMINDERS_DB = "reminders.db"

=========== تهيئة قاعدة البيانات تلقائياً ===========

def init_reminder_db(): """ ينشئ قاعدة البيانات وجدول reminders إذا لم تكن موجودة. """ conn = sqlite3.connect(REMINDERS_DB) c = conn.cursor() c.execute(""" CREATE TABLE IF NOT EXISTS reminders ( id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL, type TEXT NOT NULL, value TEXT, remind_at TEXT NOT NULL, interval_minutes INTEGER, active INTEGER DEFAULT 1 ) """) conn.commit() conn.close()

تشغيل التهيئة فور استيراد الملف

init_reminder_db()

النصّ الكامل للقائمة الرئيسية (يُعاد عند 0)

MAIN_MENU_TEXT = ( "أهلا بك في دليل خدمات القرين\n" "يمكنك الإستعلام عن الخدمات التالية:\n\n" "1️⃣ حكومي🏢\n" "2️⃣ صيدلية💊\n" "3️⃣ بقالة🥤\n" "4️⃣ خضار🥬\n" "5️⃣ رحلات⛺️\n" "6️⃣ حلا🍮\n" "7️⃣ أسر منتجة🥧\n" "8️⃣ مطاعم🍔\n" "9️⃣ قرطاسية📗\n" "🔟 محلات 🏪\n" "11- شالية\n" "12- وايت\n" "13- شيول\n" "14- دفان\n" "15- مواد بناء وعوازل\n" "16- عمال\n" "17- محلات\n" "18- ذبائح وملاحم\n" "19- نقل مدرسي ومشاوير\n" "20- منبه📆\n\n" "0️⃣ للرجوع إلى القائمة الرئيسية." )

============ الدالة الرئيسية للتعامل مع الرسائل ============

def handle(msg: str, sender: str) -> dict: text = msg.strip().lower()

# 🔙 رجوع للقائمة الرئيسية
if text == "0":
    set_session(sender, None)
    return {"reply": MAIN_MENU_TEXT}

# 🛑 إيقاف كل التنبيهات
if text == "توقف":
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
    conn.commit()
    conn.close()
    set_session(sender, None)
    return {"reply": "🛑 تم إيقاف جميع التنبيهات بنجاح."}

# جلب حالة الجلسة إن وجدت
session = get_session(sender)

# ❶ عرض قائمة المنبه
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

# ❷ في قائمة المنبه: اختيار النوع
if session == "reminder_menu":
    if text == "1":
        set_session(sender, "oil_change_duration")
        return {"reply": (
            "🛢️ كم المدة لتغيير الزيت؟\n"
            "1 = شهر\n"
            "2 = شهرين\n"
            "3 = 3 أشهر"
        )}
    if text == "3":
        set_session(sender, "istighfar_interval")
        return {"reply": (
            "🧎‍♂️ كم مرة تذكير استغفار؟\n"
            "1 = كل 30 دقيقة\n"
            "2 = كل ساعة\n"
            "3 = كل ساعتين"
        )}
    return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

# ❸ منطق تغيير الزيت
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

# ❹ منطق استغفار
if session == "istighfar_interval":
    interval_map = {"1": 30, "2": 60, "3": 120}
    if text in interval_map:
        mins = interval_map[text]
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

# افتراضي
return {"reply": "🤖 أرسل 'منبه' لعرض القائمة أو 'توقف' لإلغاء التنبيهات."}

