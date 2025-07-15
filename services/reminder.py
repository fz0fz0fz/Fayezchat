import re
import psycopg2
import os
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional, List
from services.session import get_session, set_session
from services.db import get_categories
import logging

# تهيئة السجل (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# الحصول على DATABASE_URL من متغيرات البيئة
DB_URL = os.getenv("DATABASE_URL")

def init_reminder_db() -> None:
    """Initialize the database with necessary tables if not already created."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                message TEXT,
                remind_at TIMESTAMP NOT NULL,
                interval_days INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminder_stats (
                user_id TEXT PRIMARY KEY,
                reminders_sent INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        logging.info("✅ Database initialized successfully with PostgreSQL")
    except Exception as e:
        logging.error(f"❌ Error initializing database: {e}")
    finally:
        if conn is not None:
            conn.close()
            logging.info("🔒 Database connection closed during initialization")

def save_reminder(user_id: str, reminder_type: str, message: Optional[str], remind_at: str, interval_days: int = 0) -> bool:
    """Save a new reminder to the database."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return False
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, reminder_type, message, remind_at, interval_days, active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING id
        ''', (user_id, reminder_type, message, remind_at, interval_days))
        reminder_id = cursor.fetchone()[0]
        conn.commit()
        logging.info(f"✅ Reminder saved successfully for user {user_id}, ID: {reminder_id}, Type: {reminder_type}, At: {remind_at}, Interval: {interval_days} days")
        return True
    except Exception as e:
        logging.error(f"❌ Error saving reminder for user {user_id}: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for save_reminder user {user_id}")

def delete_all_reminders(user_id: str) -> bool:
    """Delete all reminders for a user from the database."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return False
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE user_id = %s", (user_id,))
        conn.commit()
        logging.info(f"✅ All reminders deleted for user {user_id}")
        return True
    except Exception as e:
        logging.error(f"❌ Error deleting reminders for user {user_id}: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for delete_all_reminders user {user_id}")

def delete_reminder(user_id: str, reminder_id: int) -> bool:
    """Delete a specific reminder for a user."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return False
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE user_id = %s AND id = %s", (user_id, reminder_id))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"✅ Reminder {reminder_id} deleted for user {user_id}")
            return True
        else:
            logging.warning(f"❌ Reminder {reminder_id} not found for user {user_id}")
            return False
    except Exception as e:
        logging.error(f"❌ Error deleting reminder {reminder_id} for user {user_id}: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for delete_reminder user {user_id}")

def update_reminder(user_id: str, reminder_id: int, remind_at: Optional[str] = None, message: Optional[str] = None, interval_days: Optional[int] = None) -> bool:
    """Update a specific reminder for a user."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return False
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        updates = []
        values = []
        if remind_at:
            updates.append("remind_at = %s")
            values.append(remind_at)
        if message is not None:
            updates.append("message = %s")
            values.append(message)
        if interval_days is not None:
            updates.append("interval_days = %s")
            values.append(interval_days)
        if updates:
            values.extend([user_id, reminder_id])
            query = f"UPDATE reminders SET {', '.join(updates)} WHERE user_id = %s AND id = %s"
            cursor.execute(query, values)
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"✅ Reminder {reminder_id} updated for user {user_id}")
                return True
            else:
                logging.warning(f"❌ Reminder {reminder_id} not found for user {user_id}")
                return False
        else:
            logging.warning(f"❌ No updates provided for reminder {reminder_id} for user {user_id}")
            return False
    except Exception as e:
        logging.error(f"❌ Error updating reminder {reminder_id} for user {user_id}: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for update_reminder user {user_id}")

def get_current_reminders(user_id: str) -> List[Dict]:
    """Retrieve all active reminders for a user."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return []
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, reminder_type, message, remind_at, interval_days FROM reminders WHERE user_id = %s AND active = TRUE ORDER BY remind_at", (user_id,))
        reminders = cursor.fetchall()
        result = []
        for reminder in reminders:
            reminder_id, r_type, msg, remind_at, interval_days = reminder
            result.append({
                "id": reminder_id,
                "type": r_type,
                "message": msg if msg else f"تذكير: {r_type}",
                "remind_at": remind_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(remind_at, datetime) else str(remind_at),
                "interval_days": interval_days
            })
        return result
    except Exception as e:
        logging.error(f"❌ Error retrieving reminders for user {user_id}: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for get_current_reminders user {user_id}")

def get_user_stats(user_id: str) -> Dict[str, int]:
    """Retrieve user statistics about reminders."""
    conn = None
    try:
        if not DB_URL:
            logging.error("❌ DATABASE_URL not set in environment variables.")
            return {"active_count": 0, "sent_count": 0}
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reminders WHERE user_id = %s AND active = TRUE", (user_id,))
        active_count = cursor.fetchone()[0]
        cursor.execute("SELECT reminders_sent FROM reminder_stats WHERE user_id = %s", (user_id,))
        sent_row = cursor.fetchone()
        sent_count = sent_row[0] if sent_row else 0
        return {"active_count": active_count, "sent_count": sent_count}
    except Exception as e:
        logging.error(f"❌ Error retrieving stats for user {user_id}: {e}")
        return {"active_count": 0, "sent_count": 0}
    finally:
        if conn is not None:
            conn.close()
            logging.info(f"🔒 Database connection closed for get_user_stats user {user_id}")

def parse_date(text: str) -> Optional[str]:
    """Parse date input in formats like '17-08-2025' or '17/08/2025'."""
    try:
        parts = [int(p) for p in re.split(r"[-./_\\\s]+", text.strip()) if p]
        if len(parts) == 3:
            day, month, year = parts
            if year < 100:
                year += 2000
            if 1 <= month <= 12 and 1 <= day <= 31 and year >= datetime.now().year:
                return f"{year}-{month:02d}-{day:02d}"
        return None
    except Exception:
        return None

def parse_time(text: str) -> Optional[str]:
    """Parse time input in formats like '15:30'."""
    try:
        if text.lower() in ["تخطي", "skip"]:
            return "00:00"
        parts = [int(p) for p in re.split(r"[:\s]+", text.strip()) if p]
        if len(parts) == 2 and 0 <= parts[0] <= 23 and 0 <= parts[1] <= 59:
            hour, minute = parts
            return f"{hour:02d}:{minute:02d}"
        return None
    except Exception:
        return None

def parse_interval_days(text: str) -> int:
    """Parse interval text like 'كل يوم' or 'كل 3 أيام' to number of days."""
    text = text.replace("أ", "ا").replace("إ", "ا")
    patterns = [
        (r"كل\s*(\d*)\s*(يوم|أيام|days|day)", lambda m: int(m.group(1)) if m.group(1) else 1),
        (r"كل\s*(\d*)\s*(اسبوع|أسابيع|weeks|week)", lambda m: int(m.group(1)) * 7 if m.group(1) else 7),
    ]
    for pattern, func in patterns:
        match = re.search(pattern, text)
        if match:
            days = func(match)
            logging.info(f"🔁 Parsed interval '{text}' as {days} days")
            return days
    return 0  # Default to 0 (no repeat) if no valid interval is found

def get_main_menu_response() -> Dict[str, str]:
    """Return the main menu text and keyboard."""
    main_menu_text = "*_أهلا بك في دليل خدمات القرين يمكنك الإستعلام عن الخدمات التالية:_*\n\n"
    main_menu_text += "1️⃣ حكومي🏢\n"
    main_menu_text += "2️⃣ صيدلية💊\n"
    main_menu_text += "3️⃣ بقالة🥤\n"
    main_menu_text += "4️⃣ خضار🥬\n"
    main_menu_text += "5️⃣ رحلات⛺️\n"
    main_menu_text += "6️⃣ حلا🍮\n"
    main_menu_text += "7️⃣ أسر منتجة🥧\n"
    main_menu_text += "8️⃣ مطاعم🍔\n"
    main_menu_text += "9️⃣ قرطاسية📗\n"
    main_menu_text += "🔟 محلات🏪\n"
    main_menu_text += "----\n"
    main_menu_text += "11- شالية\n"
    main_menu_text += "12- وايت\n"
    main_menu_text += "13- شيول\n"
    main_menu_text += "14- دفان\n"
    main_menu_text += "15- مواد بناء وعوازل\n"
    main_menu_text += "16- عمال\n"
    main_menu_text += "17- محلات مهنية\n"
    main_menu_text += "18- ذبائح وملاحم\n"
    main_menu_text += "19- نقل مدرسي ومشاوير\n"
    main_menu_text += "20- منبه⏰\n\n"
    main_menu_text += "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
    keyboard = "حكومي||صيدلية||بقالة||خضار||رحلات||حلا||أسر منتجة||مطاعم||قرطاسية||محلات||شالية||وايت||شيول||دفان||مواد بناء وعوازل||عمال||محلات مهنية||ذبائح وملاحم||نقل مدرسي ومشاوير||منبه"
    return {"text": main_menu_text, "keyboard": keyboard}

def get_reminder_menu_response() -> Dict[str, str]:
    """Return the reminder menu text and keyboard."""
    reminder_menu_text = "⏰ *منبه*\n\n"
    reminder_menu_text += "اختر نوع التذكير الذي تريده:\n\n"
    reminder_menu_text += "1️⃣ موعد مستشفى أو مناسبة\n"
    reminder_menu_text += "2️⃣ تذكير يومي\n"
    reminder_menu_text += "3️⃣ تذكير أسبوعي\n"
    reminder_menu_text += "4️⃣ تنبيهاتي الحالية\n"
    reminder_menu_text += "5️⃣ إحصائياتي\n\n"
    reminder_menu_text += "❌ لحذف جميع التنبيهات أرسل: حذف\n"
    reminder_menu_text += "↩️ للرجوع (00) | 🏠 رئيسية (0)"
    keyboard = "1||2||3||4||5"
    return {"text": reminder_menu_text, "keyboard": keyboard}

def handle(chat_id: str, message_text: str) -> Dict[str, str]:
    """
    Handle user commands and navigate through menus in the chat.
    Returns a dictionary with response message and optional custom keyboard.
    """
    user_id = chat_id
    response = {"text": "لم أفهم طلبك. حاول مرة أخرى.", "keyboard": ""}
    
    # جلب بيانات الجلسة (قد تكون فارغة)
    session_data = get_session(user_id)
    if session_data is None:
        session_data = {}
        set_session(user_id, session_data)
    
    current_state = session_data.get("state", "")
    
    # عرض القائمة الرئيسية تلقائيًا عند بدء المحادثة
    if not current_state and not session_data.get("welcome_sent", False):
        session_data["state"] = "main_menu"
        session_data["welcome_sent"] = True
        set_session(user_id, session_data)
        return get_main_menu_response()

    # التعامل مع القائمة الرئيسية (عرضها عند الطلب)
    if message_text in ["0", "٠", "صفر", ".", "نقطة", "نقطه", "خدمات", "قائمة", "menu", "main menu", "العودة", "رجوع"]:
        session_data["state"] = "main_menu"
        set_session(user_id, session_data)
        return get_main_menu_response()
    
    # التعامل مع العودة إلى الخطوة السابقة باستخدام "00"
    if message_text == "00":
        if current_state == "reminder_menu":
            session_data["state"] = "main_menu"
            set_session(user_id, session_data)
            return get_main_menu_response()
        elif current_state == "awaiting_reminder_date":
            session_data["state"] = "reminder_menu"
            set_session(user_id, session_data)
            return get_reminder_menu_response()
        elif current_state == "awaiting_reminder_time":
            session_data["state"] = "awaiting_reminder_date"
            set_session(user_id, session_data)
            reminder_type = session_data.get("reminder_type", "موعد")
            response = {"text": f"📅 أرسل تاريخ التذكير لـ '{reminder_type}' بالميلادي:\nمثل: 17-08-2025\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)", "keyboard": ""}
        elif current_state == "awaiting_reminder_message":
            session_data["state"] = "awaiting_reminder_time"
            set_session(user_id, session_data)
            reminder_type = session_data.get("reminder_type", "موعد")
            response = {"text": f"⏰ أدخل وقت التذكير لـ '{reminder_type}' بالصيغة HH:MM (24 ساعة):\nمثل: 15:30\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)", "keyboard": ""}
        elif current_state == "awaiting_reminder_interval":
            session_data["state"] = "awaiting_reminder_message"
            set_session(user_id, session_data)
            response = {"text": "📝 هل تريد إضافة رسالة مخصصة للتذكير؟ إذا لا، اكتب 'لا' أو 'تخطي'.", "keyboard": ""}
        elif current_state == "awaiting_delete_reminder_id":
            session_data["state"] = "reminder_menu"
            set_session(user_id, session_data)
            return get_reminder_menu_response()
        elif current_state == "awaiting_edit_reminder_id":
            session_data["state"] = "reminder_menu"
            set_session(user_id, session_data)
            return get_reminder_menu_response()
        elif current_state == "awaiting_edit_reminder_date":
            session_data["state"] = "awaiting_edit_reminder_id"
            set_session(user_id, session_data)
            response = {"text": "📝 أرسل رقم التذكير الذي تريد تعديله (مثل: 1).\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)", "keyboard": ""}
        elif current_state == "awaiting_edit_reminder_time":
            session_data["state"] = "awaiting_edit_reminder_date"
            set_session(user_id, session_data)
            response = {"text": "📅 أدخل تاريخ جديد للتذكير بالميلادي (أو 'تخطي' للاحتفاظ بالتاريخ الحالي):\nمثل: 17-08-2025\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)", "keyboard": ""}
        elif current_state == "awaiting_edit_reminder_message":
            session_data["state"] = "awaiting_edit_reminder_time"
            set_session(user_id, session_data)
            response = {"text": "⏰ أدخل وقت التذكير الجديد بالصيغة HH:MM (24 ساعة):\nمثل: 15:30 أو أرسل 'تخطي' للاحتفاظ بالوقت الحالي\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)", "keyboard": ""}
        elif current_state == "awaiting_edit_reminder_interval":
            session_data["state"] = "awaiting_edit_reminder_message"
            set_session(user_id, session_data)
            response = {"text": "📝 أدخل رسالة مخصصة جديدة للتذكير (اختياري، أرسل 'تخطي' للاحتفاظ بالرسالة الحالية):\nمثل: لا تنسَ زيارة الطبيب\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)", "keyboard": ""}
        elif current_state.startswith("sub_service_"):
            session_data["state"] = "main_menu"
            set_session(user_id, session_data)
            return get_main_menu_response()
        elif current_state.startswith("service_"):
            session_data["state"] = "main_menu"
            set_session(user_id, session_data)
            return get_main_menu_response()
        else:
            response = {"text": "أنت بالفعل في القائمة الرئيسية. اكتب 'قائمة' أو '0' لعرض الخيارات.", "keyboard": ""}
        return response

    # التعامل مع اختيارات القائمة الرئيسية
    if current_state == "main_menu" or message_text in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
                                                        "حكومي", "صيدلية", "بقالة", "خضار", "رحلات", "حلا", "أسر منتجة", "مطاعم", "قرطاسية", "محلات",
                                                        "شالية", "وايت", "شيول", "دفان", "مواد بناء وعوازل", "عمال", "محلات مهنية", "ذبائح وملاحم", "نقل مدرسي ومشاوير", "منبه"]:
        service_mapping = {
            "1": "حكومي", "2": "صيدلية", "3": "بقالة", "4": "خضار", "5": "رحلات",
            "6": "حلا", "7": "أسر منتجة", "8": "مطاعم", "9": "قرطاسية", "10": "محلات",
            "11": "شالية", "12": "وايت", "13": "شيول", "14": "دفان", "15": "مواد بناء وعوازل",
            "16": "عمال", "17": "محلات مهنية", "18": "ذبائح وملاحم", "19": "نقل مدرسي ومشاوير", "20": "منبه"
        }
        selected_service = None
        # تحديد الخدمة بناءً على الرقم أو الاسم
        if message_text in service_mapping:
            selected_service = service_mapping[message_text]
        else:
            for service_name in service_mapping.values():
                if service_name in message_text or message_text.lower() in service_name.lower():
                    selected_service = service_name
                    break
        
        if selected_service:
            if selected_service == "منبه":
                session_data["state"] = "reminder_menu"
                set_session(user_id, session_data)
                return get_reminder_menu_response()
            elif selected_service == "صيدلية":
                session_data["state"] = f"service_{selected_service}"
                set_session(user_id, session_data)
                categories = get_categories()
                pharmacies = [cat for cat in categories if "صيدلية" in str(cat.get("code", ""))]
                response_text = f"🏥 قائمة الصيدليات:\nاختر صيدلية للحصول على معلومات:\n"
                keyboard_items = []
                for i, pharmacy in enumerate(pharmacies, 1):
                    response_text += f"{i}. {pharmacy.get('name', 'صيدلية غير معروفة')}\n"
                    keyboard_items.append(f"{pharmacy.get('name', str(i))}")
                response_text += "\nللرجوع إلى القائمة الرئيسية اضغط 0"
                keyboard = "||".join(keyboard_items) + "||0" if keyboard_items else "0"
                response = {"text": response_text, "keyboard": keyboard}
            else:
                session_data["state"] = f"service_{selected_service}"
                set
