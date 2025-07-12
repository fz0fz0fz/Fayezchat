# services/reminder.py
import os, re, sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session

# ───────────────────────────────────────────
# قاعدة البيانات
# ───────────────────────────────────────────
REMINDERS_DB = os.getenv("REMINDERS_DB_PATH", "reminders.db")

def init_reminder_db():
    """
    تُنشئ جدول reminders إذا لم يكن موجودًا.
    يستدعيها main.py مرة واحدة عند الإقلاع.
    """
    conn = sqlite3.connect(REMINDERS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender           TEXT NOT NULL,
            type             TEXT NOT NULL,
            interval_minutes INTEGER,
            remind_at        TEXT NOT NULL,
            active           INTEGER DEFAULT 1
        );
    """)
    conn.commit(); conn.close()

# ───────────────────────────────────────────
# نصوص القوائم
# ───────────────────────────────────────────
MAIN_MENU_TEXT = (
    "*أهلاً بك في دليل خدمات القرين*\n"
    "يمكنك الاستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي 🏢\n"
    "20- منبّه 📆"
)

REMINDER_MENU_TEXT = (
    "⏰ *منبّه*\n"
    "اختر نوع التذكير الذي تريده:\n\n"
    "2️⃣ موعد مستشفى أو مناسبة\n"
    "6️⃣ تنبيهاتي الحالية\n\n"
    "❌ لحذف جميع التنبيهات أرسل: حذف\n"
    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
)

# ───────────────────────────────────────────
# دوال مساعدة لقاعدة البيانات
# ───────────────────────────────────────────
def save_reminder(sender, typ, interval, remind_at):
    with sqlite3.connect(REMINDERS_DB) as conn:
        conn.execute(
            "INSERT INTO reminders (sender, type, interval_minutes, remind_at) VALUES (?,?,?,?)",
            (sender, typ, interval, remind_at)
        )

def list_user_reminders(sender):
    with sqlite3.connect(REMINDERS_DB) as conn:
        rows = conn.execute(
            "SELECT type, remind_at FROM reminders WHERE sender = ? AND active = 1",
            (sender,)
        ).fetchall()

    if not rows:
        return {"reply": "📭 لا توجد أي تنبيهات حالياً.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    reply = "*📋 قائمة تنبيهاتك:*\n"
    for i, (typ, at) in enumerate(rows, 1):
        reply += f"{i}- نوع: {typ} | التاريخ: {at}\n"
    reply += "\n❌ لحذف جميع التنبيهات أرسل: حذف\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
    return {"reply": reply}

def delete_all_reminders(sender):
    with sqlite3.connect(REMINDERS_DB) as conn:
        conn.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
    return {"reply": "✅ تم حذف جميع التنبيهات بنجاح.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

# ───────────────────────────────────────────
# الدالّة الرئيسـيـة
# ───────────────────────────────────────────
def handle(msg: str, sender: str) -> dict:
    session = get_session(sender)
    text    = msg.strip()

    # ---------- مفاتيح عامّة ----------
    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    if text == "00":
        if session and session.get("last_menu"):
            last = session["last_menu"]
            set_session(sender, {"menu": last, "last_menu": "main"})
            return handle(last, sender)
        return {"reply": MAIN_MENU_TEXT}

    if text == "حذف":
        return delete_all_reminders(sender)

    # ---------- بدون جلسة ----------
    if session is None:
        if text == "20":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        return {"reply": MAIN_MENU_TEXT}

    # ---------- قائمة المنبّه ----------
    if session["menu"] == "reminder_main":
        if text == "2":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main"})
            return {"reply": (
                "📅 أرسل تاريخ الموعد بالميلادي فقط :\n"
                "مثل: 17-08-2025\n"
                "وسيتم تذكيرك قبل الموعد بيوم واحد\n\n"
                "↩️ للرجوع (00) | 🏠 رئيسية (0)"
            )}
        if text == "6":
            return list_user_reminders(sender)
        return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

    # ---------- إدخال التاريخ ----------
    if session["menu"] == "reminder_date":
        try:
            parts = [int(p) for p in re.split(r"[-./_\\\s]+", text) if p]
            if len(parts) != 3:
                raise ValueError
            day, month, year = parts
            if year < 100: year += 2000
            date_obj  = datetime(year, month, day)
            remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
            save_reminder(sender, "hospital", None, remind_at)
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": f"✅ تم ضبط التذكير، سيتم التذكير بتاريخ {remind_at}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        except Exception:
            return {"reply": "❗️صيغة غير صحيحة. أرسل التاريخ مثل: 17-08-2025\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    return {"reply": MAIN_MENU_TEXT}
