# services/reminder.py
import re
import sqlite3
from datetime import datetime, timedelta
from services.session import get_session, set_session
from services.db import get_categories

DB_PATH = "reminders.db"

# ============ إنشاء الجدول إن لم يكن موجودًا ============
def init_reminder_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                message TEXT,
                remind_at TEXT NOT NULL,
                interval_days INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminder_stats (
                user_id TEXT NOT NULL,
                reminders_sent INTEGER DEFAULT 0,
                PRIMARY KEY (user_id)
            )
        ''')
        conn.commit()
        print("✅ تم إنشاء قاعدة البيانات reminders.db إن لم تكن موجودة.")
    except Exception as e:
        print(f"❌ خطأ أثناء إنشاء قاعدة البيانات: {e}")
    finally:
        conn.close()

# ============ حفظ تذكير جديد ============
def save_reminder(user_id, reminder_type, message, remind_at, interval_days=0):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, type, message, remind_at, interval_days, active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (user_id, reminder_type, message, remind_at, interval_days))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ أثناء حفظ التذكير: {e}")
        return False
    finally:
        conn.close()

# ============ حذف جميع التذكيرات ============
def delete_all_reminders(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE user_id = ?', (user_id,))
        conn.commit()
        return {"reply": "✅ تم حذف جميع التذكيرات الخاصة بك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    except Exception as e:
        return {"reply": f"❌ خطأ أثناء حذف التذكيرات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        conn.close()

# ============ حذف تذكير محدد ============
def delete_reminder(user_id, reminder_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE user_id = ? AND id = ?', (user_id, reminder_id))
        conn.commit()
        if cursor.rowcount > 0:
            return {"reply": f"✅ تم حذف التذكير رقم {reminder_id} بنجاح.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            return {"reply": f"❌ التذكير رقم {reminder_id} غير موجود أو لا يخصك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    except Exception as e:
        return {"reply": f"❌ خطأ أثناء حذف التذكير: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        conn.close()

# ============ تعديل تذكير محدد ============
def update_reminder(user_id, reminder_id, remind_at=None, message=None, interval_days=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        updates = []
        values = []
        if remind_at:
            updates.append("remind_at = ?")
            values.append(remind_at)
        if message is not None:  # Allow empty string as input
            updates.append("message = ?")
            values.append(message)
        if interval_days is not None:
            updates.append("interval_days = ?")
            values.append(interval_days)
        if updates:
            values.extend([user_id, reminder_id])
            query = f"UPDATE reminders SET {', '.join(updates)} WHERE user_id = ? AND id = ?"
            cursor.execute(query, values)
            conn.commit()
            if cursor.rowcount > 0:
                return {"reply": f"✅ تم تعديل التذكير رقم {reminder_id} بنجاح.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
            else:
                return {"reply": f"❌ التذكير رقم {reminder_id} غير موجود أو لا يخصك.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
        else:
            return {"reply": "❌ لم يتم تقديم أي بيانات للتعديل.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    except Exception as e:
        return {"reply": f"❌ خطأ أثناء تعديل التذكير: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
    finally:
        conn.close()

# ============ عرض تذكيرات المستخدم ============
def list_user_reminders(user_id, sender):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, type, remind_at, interval_days FROM reminders WHERE user_id = ? AND active = 1', (user_id,))
        rows = cursor.fetchall()

        if not rows:
            reply = "📭 لا توجد أي تنبيهات نشطة حاليًا.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
            set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
            return {"reply": reply}

        reply = "🔔 تنبيهاتك النشطة الحالية:\n\n"
        for row in rows:
            interval_text = f" (يتكرر كل {row[3]} يوم)" if row[3] > 0 else ""
            reply += f"{row[0]} - {row[1]}{interval_text} بتاريخ {row[2]}\n"
        reply += "\nاختر خيارًا:\n- أرسل 'حذف <رقم>' لحذف تذكير (مثل: حذف 1)\n- أرسل 'تعديل <رقم>' لتعديل تذكير (مثل: تعديل 2)\n"
        reply += "↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        return {"reply": reply}
    except Exception as e:
        reply = f"❌ خطأ أثناء عرض التذكيرات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        return {"reply": reply}
    finally:
        conn.close()

# ============ عرض إحصائيات المستخدم ============
def get_user_stats(user_id, sender):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # عدد التذكيرات النشطة
        cursor.execute('SELECT COUNT(*) FROM reminders WHERE user_id = ? AND active = 1', (user_id,))
        active_count = cursor.fetchone()[0]
        # عدد التذكيرات المرسلة (من جدول الإحصائيات)
        cursor.execute('SELECT reminders_sent FROM reminder_stats WHERE user_id = ?', (user_id,))
        sent_row = cursor.fetchone()
        sent_count = sent_row[0] if sent_row else 0
        
        reply = f"📊 *إحصائياتك الشخصية:*\n- التذكيرات النشطة: {active_count}\n- التذكيرات المرسلة: {sent_count}\n\n"
        reply += "↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        return {"reply": reply}
    except Exception as e:
        reply = f"❌ خطأ أثناء عرض الإحصائيات: {str(e)}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
        set_session(sender, {"menu": "reminder_main", "last_menu": "reminder_main"})
        return {"reply": reply}
    finally:
        conn.close()

# ============ القوائم ============
REMINDER_MENU_TEXT = (
    "⏰ *منبه*\n\n"
    "اختر نوع التذكير الذي تريده:\n\n"
    "1️⃣ موعد مستشفى أو مناسبة\n"
    "2️⃣ تذكير يومي\n"
    "3️⃣ تذكير أسبوعي\n"
    "4️⃣ تنبيهاتي الحالية\n"
    "5️⃣ إحصائياتي\n\n"
    "❌ لحذف جميع التنبيهات أرسل: حذف\n"
    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
)

MAIN_MENU_TEXT = (
    "*أهلاً بك في دليل خدمات القرين*\n"
    "يمكنك الاستعلام عن الخدمات التالية:\n\n"
    "1️⃣ حكومي🏢\n"
    "2️⃣ منبه 📆\n"
    "3️⃣ صيدليات 💊"
)

# ============ المعالجة الرئيسية ============
def handle(msg: str, sender: str) -> dict:
    session = get_session(sender)
    text = msg.strip()

    if text == "0":
        # إعادة تعيين الجلسة بالكامل عند اختيار العودة إلى القائمة الرئيسية
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    if text == "00":
        # الرجوع إلى القائمة السابقة بناءً على last_menu
        if session and "last_menu" in session:
            last_menu = session.get("last_menu", "main")
            if last_menu == "main" or last_menu == "":
                set_session(sender, None)
                return {"reply": MAIN_MENU_TEXT}
            elif last_menu == "reminder_main":
                set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
                return {"reply": REMINDER_MENU_TEXT}
            elif last_menu == "reminder_date":
                set_session(sender, {
                    "menu": "reminder_date",
                    "last_menu": "reminder_main",
                    "reminder_type": session.get("reminder_type", "موعد"),
                    "interval_days": session.get("interval_days", 0)
                })
                return {
                    "reply": (
                        "📅 أرسل تاريخ التذكير بالميلادي:\n"
                        "مثل: 17-08-2025\n\n"
                        "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                    )
                }
            elif last_menu == "reminder_time":
                set_session(sender, {
                    "menu": "reminder_time",
                    "last_menu": "reminder_date",
                    "reminder_type": session.get("reminder_type", "موعد"),
                    "interval_days": session.get("interval_days", 0),
                    "date": session.get("date", "2023-01-01")
                })
                return {
                    "reply": (
                        "⏰ أدخل وقت التذكير بالصيغة HH:MM (24 ساعة):\n"
                        "مثل: 15:30\n\n"
                        "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                    )
                }
            elif last_menu == "reminder_message":
                set_session(sender, {
                    "menu": "reminder_message",
                    "last_menu": "reminder_time",
                    "reminder_type": session.get("reminder_type", "موعد"),
                    "interval_days": session.get("interval_days", 0),
                    "date": session.get("date", "2023-01-01"),
                    "time": session.get("time", "00:00")
                })
                return {
                    "reply": (
                        "📝 أدخل رسالة مخصصة للتذكير (اختياري، أرسل 'تخطي' إذا لا تريد):\n"
                        "مثل: لا تنسَ زيارة الطبيب\n\n"
                        "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                    )
                }
            elif "reminder_edit" in last_menu:
                set_session(sender, {
                    "menu": last_menu,
                    "last_menu": "reminder_main",
                    "reminder_id": session.get("reminder_id", None),
                    "date": session.get("date", "2023-01-01") if "date" in session else "2023-01-01",
                    "time": session.get("time", "00:00") if "time" in session else "00:00",
                    "remind_at": session.get("remind_at", "") if "remind_at" in session else ""
                })
                if last_menu == "reminder_edit":
                    return {
                        "reply": (
                            "📅 أدخل تاريخ جديد للتذكير بالميلادي (أو 'تخطي' للاحتفاظ بالتاريخ الحالي):\n"
                            "مثل: 17-08-2025\n\n"
                            "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                        )
                    }
                elif last_menu == "reminder_edit_time":
                    return {
                        "reply": (
                            "⏰ أدخل وقت التذكير الجديد بالصيغة HH:MM (24 ساعة):\n"
                            "مثل: 15:30 أو أرسل 'تخطي' للاحتفاظ بالوقت الحالي\n\n"
                            "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                        )
                    }
                elif last_menu == "reminder_edit_message":
                    return {
                        "reply": (
                            "📝 أدخل رسالة مخصصة جديدة للتذكير (اختياري، أرسل 'تخطي' للاحتفاظ بالرسالة الحالية):\n"
                            "مثل: لا تنسَ زيارة الطبيب\n\n"
                            "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                        )
                    }
            else:
                # إذا لم تكن القائمة السابقة معروفة، نعود إلى القائمة الرئيسية
                set_session(sender, None)
                return {"reply": MAIN_MENU_TEXT}
        else:
            # إذا لم تكن هناك جلسة أو last_menu، نعود إلى القائمة الرئيسية
            set_session(sender, None)
            return {"reply": MAIN_MENU_TEXT}

    if text.lower() == "حذف":
        result = delete_all_reminders(sender)
        set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
        return result

    # إذا لم تكن هناك جلسة (أي في القائمة الرئيسية)
    if session is None or not session:
        if text == "2":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        elif text == "3":
            categories = get_categories()
            if not categories:
                return {"reply": "❌ لا توجد بيانات متاحة عن الصيدليات حاليًا.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}
            
            reply = "💊 *قائمة الصيدليات:*\n\n"
            for category in categories:
                code, name, description, morning_start, morning_end, evening_start, evening_end = category
                reply += f"🏢 *{name}*\n"
                reply += f"{description}\n"
                reply += f"⏰ *دوام الصباح*: {morning_start} - {morning_end}\n"
                reply += f"⏰ *دوام المساء*: {evening_start} - {evening_end}\n\n"
            reply += "↩️ للرجوع (00) | 🏠 رئيسية (0)"
            return {"reply": reply}
        else:
            return {"reply": MAIN_MENU_TEXT}

    current_menu = session.get("menu", "reminder_main")

    if current_menu == "reminder_main":
        if text == "1":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main", "reminder_type": "موعد", "interval_days": 0})
            return {
                "reply": (
                    "📅 أرسل تاريخ الموعد بالميلادي فقط:\n"
                    "مثل: 17-08-2025\n"
                    "وسيتم تذكيرك قبل الموعد بيوم واحد\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "2":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main", "reminder_type": "يومي", "interval_days": 1})
            return {
                "reply": (
                    "📅 أرسل تاريخ بدء التذكير اليومي بالميلادي:\n"
                    "مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "3":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main", "reminder_type": "أسبوعي", "interval_days": 7})
            return {
                "reply": (
                    "📅 أرسل تاريخ بدء التذكير الأسبوعي بالميلادي:\n"
                    "مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "4":
            result = list_user_reminders(sender, sender)
            return {"reply": result["reply"]}
        elif text == "5":
            result = get_user_stats(sender, sender)
            return {"reply": result["reply"]}
        else:
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": "↩️ اختر رقم صحيح أو أرسل 'حذف' لإزالة جميع التنبيهات.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    elif current_menu == "reminder_date":
        try:
            parts = [int(p) for p in re.split(r"[-./_\\\s]+", text.strip()) if p]
            if len(parts) == 3:
                day, month, year = parts
                if year < 100: year += 2000
                set_session(sender, {
                    "menu": "reminder_time",
                    "last_menu": "reminder_date",
                    "reminder_type": session.get("reminder_type", "موعد"),
                    "interval_days": session.get("interval_days", 0),
                    "date": f"{year}-{month:02d}-{day:02d}"
                })
                return {
                    "reply": (
                        "⏰ أدخل وقت التذكير بالصيغة HH:MM (24 ساعة):\n"
                        "مثل: 15:30\n\n"
                        "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                    )
                }
            else:
                raise ValueError
        except Exception as e:
            return {
                "reply": (
                    "❗️ صيغة غير صحيحة. أرسل التاريخ مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }

    elif current_menu == "reminder_time":
        try:
            if text.lower() in ["تخطي", "skip"]:
                hour, minute = 0, 0
            else:
                parts = [int(p) for p in re.split(r"[:\s]+", text.strip()) if p]
                if len(parts) == 2 and 0 <= parts[0] <= 23 and 0 <= parts[1] <= 59:
                    hour, minute = parts
                else:
                    raise ValueError
            set_session(sender, {
                "menu": "reminder_message",
                "last_menu": "reminder_time",
                "reminder_type": session.get("reminder_type", "موعد"),
                "interval_days": session.get("interval_days", 0),
                "date": session.get("date", "2023-01-01"),
                "time": f"{hour:02d}:{minute:02d}"
            })
            return {
                "reply": (
                    "📝 أدخل رسالة مخصصة للتذكير (اختياري، أرسل 'تخطي' إذا لا تريد):\n"
                    "مثل: لا تنسَ زيارة الطبيب\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        except Exception as e:
            return {
                "reply": (
                    "❗️ صيغة غير صحيحة. أرسل الوقت مثل: 15:30 أو 'تخطي'\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }

    elif current_menu == "reminder_message":
        reminder_type = session.get("reminder_type", "موعد")
        interval_days = session.get("interval_days", 0)
        date_str = session.get("date", "2023-01-01")
        time_str = session.get("time", "00:00")
        remind_at = f"{date_str} {time_str}:00"
        if reminder_type == "موعد":
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d") + f" {time_str}:00"
        message = None if text.lower() in ["تخطي", "skip"] else text
        if save_reminder(sender, reminder_type, message, remind_at, interval_days):
            repeat_text = f"يتكرر كل {interval_days} يوم" if interval_days > 0 else "لن يتكرر"
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {
                "reply": f"✅ تم ضبط التذكير بنجاح لـ '{reminder_type}' بتاريخ {remind_at}\n"
                         f"التكرار: {repeat_text}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
            }
        else:
            return {
                "reply": f"❌ حدث خطأ أثناء ضبط التذكير. حاول مرة أخرى.\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
            }

    elif current_menu == "reminder_edit":
        reminder_id = session.get("reminder_id")
        if text.lower() in ["تخطي", "skip"]:
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return update_reminder(sender, reminder_id)
        try:
            parts = [int(p) for p in re.split(r"[-./_\\\s]+", text.strip()) if p]
            if len(parts) == 3:
                day, month, year = parts
                if year < 100: year += 2000
                date_str = f"{year}-{month:02d}-{day:02d}"
                set_session(sender, {
                    "menu": "reminder_edit_time",
                    "last_menu": "reminder_edit",
                    "reminder_id": reminder_id,
                    "date": date_str
                })
                return {
                    "reply": (
                        "⏰ أدخل وقت التذكير الجديد بالصيغة HH:MM (24 ساعة):\n"
                        "مثل: 15:30 أو أرسل 'تخطي' للاحتفاظ بالوقت الحالي\n\n"
                        "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                    )
                }
            else:
                raise ValueError
        except Exception as e:
            return {
                "reply": (
                    "❗️ صيغة غير صحيحة. أرسل التاريخ مثل: 17-08-2025 أو 'تخطي'\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }

    elif current_menu == "reminder_edit_time":
        reminder_id = session.get("reminder_id")
        date_str = session.get("date")
        if text.lower() in ["تخطي", "skip"]:
            remind_at = None  # Skip time update
        else:
            try:
                parts = [int(p) for p in re.split(r"[:\s]+", text.strip()) if p]
                if len(parts) == 2 and 0 <= parts[0] <= 23 and 0 <= parts[1] <= 59:
                    hour, minute = parts
                    remind_at = f"{date_str} {hour:02d}:{minute:02d}:00"
                else:
                    raise ValueError
            except Exception as e:
                return {
                    "reply": (
                        "❗️ صيغة غير صحيحة. أرسل الوقت مثل: 15:30 أو 'تخطي'\n\n"
                        "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                    )
                }
        set_session(sender, {
            "menu": "reminder_edit_message",
            "last_menu": "reminder_edit_time",
            "reminder_id": reminder_id,
            "remind_at": remind_at if remind_at else ""
        })
        return {
            "reply": (
                "📝 أدخل رسالة مخصصة جديدة للتذكير (اختياري، أرسل 'تخطي' للاحتفاظ بالرسالة الحالية):\n"
                "مثل: لا تنسَ زيارة الطبيب\n\n"
                "↩️ للرجوع (00) | 🏠 رئيسية (0)"
            )
        }

    elif current_menu == "reminder_edit_message":
        reminder_id = session.get("reminder_id")
        remind_at = session.get("remind_at") if session.get("remind_at") else None
        message = None if text.lower() in ["تخطي", "skip"] else text
        set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
        return update_reminder(sender, reminder_id, remind_at=remind_at, message=message)

    # التعامل مع أوامر حذف أو تعديل تذكير محدد
    if text.lower().startswith("حذف "):
        try:
            reminder_id = int(text.split()[1])
            result = delete_reminder(sender, reminder_id)
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return result
        except (IndexError, ValueError):
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": "❌ صيغة غير صحيحة. أرسل 'حذف <رقم>' مثل: حذف 1\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    if text.lower().startswith("تعديل "):
        try:
            reminder_id = int(text.split()[1])
            set_session(sender, {
                "menu": "reminder_edit",
                "last_menu": "reminder_main",
                "reminder_id": reminder_id
            })
            return {
                "reply": (
                    "📅 أدخل تاريخ جديد للتذكير بالميلادي (أو 'تخطي' للاحتفاظ بالتاريخ الحالي):\n"
                    "مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        except (IndexError, ValueError):
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": "❌ صيغة غير صحيحة. أرسل 'تعديل <رقم>' مثل: تعديل 2\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"}

    # إذا لم يتم التعرف على المدخلات، إعادة تعيين الجلسة كاحتياط
    set_session(sender, None)
    return {"reply": MAIN_MENU_TEXT}
