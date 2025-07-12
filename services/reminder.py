import os import re import sqlite3 from datetime import datetime, timedelta from services.session import get_session, set_session

مسار قاعدة البيانات (يمكن تغييره من متغيرات البيئة في Render)

REMINDERS_DB = os.getenv("REMINDERS_DB_PATH", "reminders.db")

def init_reminder_db() -> None: """إنشاء جدول التذكيرات عند التشغيل لأول مرّة (إن لم يكن موجودًا).""" conn = sqlite3.connect(REMINDERS_DB) c = conn.cursor() c.execute( """ CREATE TABLE IF NOT EXISTS reminders ( id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL, type   TEXT NOT NULL, interval_minutes INTEGER, remind_at TEXT NOT NULL, active  INTEGER DEFAULT 1 ) """ ) conn.commit() conn.close()

---------- أداة عرض التنبيهات الحالية ----------

def list_reminders(sender: str) -> dict: """إرجاع رسالة بكل التذكيرات النشطة لهذا المستخدم.""" with sqlite3.connect(REMINDERS_DB) as conn: rows = conn.execute( "SELECT id, type, remind_at, interval_minutes FROM reminders WHERE sender = ? AND active = 1", (sender,) ).fetchall()

if not rows:
    return {"reply": "❌ لا يوجد لديك أي تنبيهات حالياً."}

msg = "📋 تنبيهاتك الحالية:\n\n"
for idx, (rid, r_type, r_date, interval) in enumerate(rows, start=1):
    line = f"{idx}️⃣ {r_type}"
    if r_date:
        line += f" → {r_date.split(' ')[0]}"
    if interval:
        line += f" (كل {interval} دقيقة)"
    msg += line + "\n"

msg += "\n✏️ لحذف أحدها أرسل: حذف 1\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
return {"reply": msg}

نص القائمة الرئيسيّة

MAIN_MENU_TEXT = ( "أهلا بك في دليل خدمات القرين\n" "يمكنك الإستعلام عن الخدمات التالية:\n\n" "1️⃣ حكومي🏢\n" "20- منبه📆" )

————————————————————————————————————————————————

def handle(msg: str, sender: str): """المعالج الرئيسي للمنبّه.""" text = msg.strip().lower() session = get_session(sender)

# عرض جميع التنبيهات
if text in {"قائمة", "تنبيهاتي", "list"}:
    return list_reminders(sender)

# الرجوع للقائمة الرئيسيّة
if text == "0":
    set_session(sender, None)
    return {"reply": MAIN_MENU_TEXT}

# إيقاف جميع التنبيهات
if text == "توقف":
    with sqlite3.connect(REMINDERS_DB) as conn:
        conn.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
    set_session(sender, None)
    return {"reply": "🛑 تم إيقاف جميع التنبيهات بنجاح."}

# ——— القائمة الأولى للمنبّه ———
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
            "📅 أرسل تاريخ الموعد بالميلادي فقط :\n"
            "مثال: 17-08-2025\n"
            "وسيتم تذكيرك قبل الموعد بيوم واحد\n\n"
            "↩️ للرجوع (00) | 🏠 رئيسية (0)"
        )}
    if text == "3":
        set_session(sender, "istighfar_interval")
        return {"reply": (
            "🧎‍♂️ كم مرة تذكير استغفار؟\n"
            "1 = كل 30 دقيقة\n2 = كل ساعة\n3 = كل ساعتين\n\n"
            "↩️ للرجوع (00) | 🏠 رئيسية (0)"
        )}
    return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

# ——— منطق تغيير الزيت ———
if session == "oil_change_duration":
    if text == "00":
        set_session(sender, "reminder_menu")
        return handle("20", sender)
    if text in {"1", "2", "3"}:
        months = int(text)
        remind_time = datetime.now() + timedelta(days=30 * months)
        with sqlite3.connect(REMINDERS_DB) as conn:
            conn.execute(
                "INSERT INTO reminders (sender, type, remind_at) VALUES (?,?,?)",
                (sender, "تغيير الزيت", remind_time.strftime("%Y-%m-%d %H:%M:%S"))
            )
        set_session(sender, None)
        return {"reply": f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."}
    return {"reply": "📌 اختر 1 أو 2 أو 3."}

# ——— منطق موعد المستشفى/المناسبة ———
if session == "appointment_date":
    if text == "00":
        set_session(sender, "reminder_menu")
        return handle("20", sender)
    match = re.fullmatch(r"\s*(\d{1,2})\s*[-/.\\ _]\s*(\d{1,2})\s*[-/.\\ _]\s*(\d{4})\s*", text)
    if match:
        day, month, year = map(int, match.groups())
        try:
            date_obj = datetime(year, month, day)
            remind_at = date_obj - timedelta(days=1)
            with sqlite3.connect(REMINDERS_DB) as conn:
                conn.execute(
                    "INSERT INTO reminders (sender, type, remind_at) VALUES (?,?,?)",
                    (sender, "موعد مستشفى أو مناسبة", remind_at.strftime("%Y-%m-%d %H:%M:%S"))
                )
            set_session(sender, None)
            return {"reply": f"✅ تم ضبط التذكير، سيتم تنبيهك يوم {remind_at.date()} بإذن الله."}
        except ValueError:
            pass  # تاريخ غير صالح
    return {"reply": "❌ صيغة التاريخ غير صحيحة. مثال: 17-08-2025"}

# ——— منطق استغفار دوري ———
if session == "istighfar_interval":
    if text == "00":
        set_session(sender, "reminder_menu")
        return handle("20", sender)
    mapping = {"1": 30, "2": 60, "3": 120}
    if text in mapping:
        mins = mapping[text]
        remind_at = datetime.now() + timedelta(minutes=mins)
        with sqlite3.connect(REMINDERS_DB) as conn:
            conn.execute(
                "INSERT INTO reminders (sender, type, interval_minutes, remind_at) VALUES (?,?,?,?)",
                (sender, "استغفار",

