from typing import Dict, List
import psycopg2
import os
import re
from datetime import datetime, timedelta
import pytz
from .session import get_session, set_session
from .db import get_categories
from .db_pool import get_db_connection, close_db_connection
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def init_reminder_db(conn=None):
    if not conn:
        conn = get_db_connection()
        if not conn:
            logging.error("❌ DATABASE_URL not set in environment variables or connection failed.")
            return
    try:
        c = conn.cursor()
        c.execute('''
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
        c.execute('''
            CREATE TABLE IF NOT EXISTS reminder_stats (
                user_id TEXT PRIMARY KEY,
                reminders_sent INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        logging.info("✅ تم إنشاء جداول reminders وreminder_stats إن لم تكن موجودة.")
    except psycopg2.DatabaseError as e:
        logging.error(f"❌ خطأ أثناء تهيئة قاعدة البيانات: {e}")
    finally:
        if not conn and conn is not None:
            close_db_connection(conn)
            logging.info("🔒 Database connection closed for init_reminder_db")

init_reminder_db()

def display_category_list(user_id: str, service: str, categories: List[Dict], session_data: Dict) -> Dict[str, str]:
    session_data["state"] = f"service_{service}"
    session_data["history"] = session_data.get("history", []) + [session_data.get("state", "main_menu")]
    set_session(user_id, session_data)
    if not categories:
        response_text = f"❌ لا توجد بيانات متاحة حاليًا للخدمة: {service}\n\n🔙 للرجوع إلى القائمة الرئيسية 🏠 اضغط 0"
        return {"text": response_text, "keyboard": "0"}
    response_text = f"📌 قائمة {service}:\nاختر خيارًا للحصول على التفاصيل:\n\n"
    keyboard_items = []
    for i, category in enumerate(categories, 1):
        response_text += f"{i}. {category.get('emoji', '📌')} {category.get('name', 'غير معروف')}\n"
        keyboard_items.append(f"{i}")
    response_text += "\n🔙 للرجوع إلى القائمة الرئيسية 🏠 اضغط 0\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
    keyboard = "||".join(keyboard_items) + "||0||00" if keyboard_items else "0||00"
    return {"text": response_text, "keyboard": keyboard}

def parse_date(date_str: str) -> datetime | None:
    formats = [
        "%Y-%m-%d",    # 2025-07-16
        "%d-%m-%Y",    # 16-07-2025
        "%m/%d/%Y",    # 07/16/2025
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=pytz.timezone("Asia/Riyadh"))
        except ValueError:
            continue
    return None

def parse_time(time_str: str) -> datetime | None:
    time_str = time_str.strip().upper()
    formats = [
        "%H:%M",       # 14:30
        "%I:%M %p",    # 02:30 PM
        "%H:%M:%S",    # 14:30:00 (اختياري)
        "%I:%M:%S %p", # 02:30:00 PM (اختياري)
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.replace(tzinfo=pytz.timezone("Asia/Riyadh"))
        except ValueError:
            continue
    return None

def handle_reminder(user_id: str, message: str, conn=None) -> Dict[str, str]:
    if not conn:
        conn = get_db_connection()
        if not conn:
            return {"text": "❌ فشل الاتصال بقاعدة البيانات.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)", "keyboard": "0"}
    
    session_data = get_session(user_id)
    current_state = session_data.get("state", "main_menu")
    history = session_data.get("history", [])
    
    if message == "0":
        session_data = {"state": "main_menu", "history": []}
        set_session(user_id, session_data)
        response_text = (
            "🌟 *أهلا بك في دليل خدمات القرين يمكنك الإستعلام عن الخدمات التالية:* 🌟\n\n"
            "1️⃣ حكومي 🏢\n2️⃣ صيدلية 💊\n3️⃣ بقالة 🥤\n4️⃣ خضار 🥬\n5️⃣ رحلات ⛺️\n"
            "6️⃣ حلا 🍮\n7️⃣ أسر منتجة 🥧\n8️⃣ مطاعم 🍔\n9️⃣ قرطاسية 📗\n🔟 محلات 🏪\n"
            "----\n11. شالية 🏖\n12. وايت 🚛\n13. شيول 🚜\n14. دفان 🏗\n15. مواد بناء وعوازل 🧱\n"
            "16. عمال 👷\n17. محلات مهنية 🔨\n18. ذبائح وملاحم 🥩\n19. نقل مدرسي ومشاوير 🚍\n20. منبه ⏰\n\n"
            "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
        )
        keyboard = "1||2||3||4||5||6||7||8||9||10||11||12||13||14||15||16||17||18||19||20"
        return {"text": response_text, "keyboard": keyboard}
    
    if message == "00" and history:
        previous_state = history.pop() if history else "main_menu"
        session_data = {"state": previous_state, "history": history}
        set_session(user_id, session_data)
        if previous_state == "main_menu":
            response_text = (
                "🌟 *أهلا بك في دليل خدمات القرين يمكنك الإستعلام عن الخدمات التالية:* 🌟\n\n"
                "1️⃣ حكومي 🏢\n2️⃣ صيدلية 💊\n3️⃣ بقالة 🥤\n4️⃣ خضار 🥬\n5️⃣ رحلات ⛺️\n"
                "6️⃣ حلا 🍮\n7️⃣ أسر منتجة 🥧\n8️⃣ مطاعم 🍔\n9️⃣ قرطاسية 📗\n🔟 محلات 🏪\n"
                "----\n11. شالية 🏖\n12. وايت 🚛\n13. شيول 🚜\n14. دفان 🏗\n15. مواد بناء وعوازل 🧱\n"
                "16. عمال 👷\n17. محلات مهنية 🔨\n18. ذبائح وملاحم 🥩\n19. نقل مدرسي ومشاوير 🚍\n20. منبه ⏰\n\n"
                "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
            )
            keyboard = "1||2||3||4||5||6||7||8||9||10||11||12||13||14||15||16||17||18||19||20"
            return {"text": response_text, "keyboard": keyboard}
        elif previous_state == "reminder_menu":
            response_text = (
                "⏰ *منبه* ⏰\n\nاختر نوع التذكير الذي تريده:\n\n1️⃣ موعد مستشفى أو مناسبة 🩺\n"
                "2️⃣ تذكير بأكل الدواء 💊\n3️⃣ منبه أذكار الصباح والمساء 📿\n4️⃣ تنبيهاتي الحالية 📜\n"
                "5️⃣ إحصائياتي 📊\n\n❌ لحذف جميع التنبيهات أرسل: حذف\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)"
            )
            return {"text": response_text, "keyboard": "1||2||3||4||5||حذف||0"}
        elif previous_state.startswith("service_"):
            service = previous_state.replace("service_", "")
            categories = get_categories()
            if service == "صيدلية":
                categories = [cat for cat in categories if "pharmacy" in cat.get("code", "").lower()]
            return display_category_list(user_id, service, categories, session_data)
    
    if current_state == "main_menu":
        services = {
            "1": "حكومي", "2": "صيدلية", "3": "بقالة", "4": "خضار", "5": "رحلات",
            "6": "حلا", "7": "أسر منتجة", "8": "مطاعم", "9": "قرطاسية", "10": "محلات",
            "11": "شالية", "12": "وايت", "13": "شيول", "14": "دفان", "15": "مواد بناء وعوازل",
            "16": "عمال", "17": "محلات مهنية", "18": "ذبائح وملاحم", "19": "نقل مدرسي ومشاوير", "20": "منبه"
        }
        service_names = {v: k for k, v in services.items()}
        selected_service = services.get(message) or service_names.get(message.lower())
        
        if selected_service:
            if selected_service == "منبه":
                session_data["state"] = "reminder_menu"
                session_data["history"] = history + [current_state]
                set_session(user_id, session_data)
                response_text = (
                    "⏰ *منبه* ⏰\n\nاختر نوع التذكير الذي تريده:\n\n1️⃣ موعد مستشفى أو مناسبة 🩺\n"
                    "2️⃣ تذكير بأكل الدواء 💊\n3️⃣ منبه أذكار الصباح والمساء 📿\n4️⃣ تنبيهاتي الحالية 📜\n"
                    "5️⃣ إحصائياتي 📊\n\n❌ لحذف جميع التنبيهات أرسل: حذف\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)"
                )
                return {"text": response_text, "keyboard": "1||2||3||4||5||حذف||0"}
            elif selected_service == "صيدلية":
                categories = get_categories()
                pharmacies = [cat for cat in categories if "pharmacy" in cat.get("code", "").lower()]
                return display_category_list(user_id, selected_service, pharmacies, session_data)
            else:
                session_data["state"] = f"service_{selected_service}"
                session_data["history"] = history + [current_state]
                set_session(user_id, session_data)
                response_text = f"⚙️ الخدمة '{selected_service}' قيد التطوير.\n\n🔙 للرجوع إلى القائمة الرئيسية 🏠 اضغط 0\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                return {"text": response_text, "keyboard": "0||00"}
        response_text = (
            "🌟 *أهلا بك في دليل خدمات القرين يمكنك الإستعلام عن الخدمات التالية:* 🌟\n\n"
            "1️⃣ حكومي 🏢\n2️⃣ صيدلية 💊\n3️⃣ بقالة 🥤\n4️⃣ خضار 🥬\n5️⃣ رحلات ⛺️\n"
            "6️⃣ حلا 🍮\n7️⃣ أسر منتجة 🥧\n8️⃣ مطاعم 🍔\n9️⃣ قرطاسية 📗\n🔟 محلات 🏪\n"
            "----\n11. شالية 🏖\n12. وايت 🚛\n13. شيول 🚜\n14. دفان 🏗\n15. مواد بناء وعوازل 🧱\n"
            "16. عمال 👷\n17. محلات مهنية 🔨\n18. ذبائح وملاحم 🥩\n19. نقل مدرسي ومشاوير 🚍\n20. منبه ⏰\n\n"
            "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
        )
        keyboard = "1||2||3||4||5||6||7||8||9||10||11||12||13||14||15||16||17||18||19||20"
        return {"text": response_text, "keyboard": keyboard}
    
    elif current_state == "reminder_menu":
        if message == "حذف":
            try:
                c = conn.cursor()
                c.execute('UPDATE reminders SET active = FALSE WHERE user_id = %s', (user_id,))
                conn.commit()
                response_text = "🗑 تم حذف جميع التنبيهات بنجاح!\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                session_data = {"state": "reminder_menu", "history": history}
                set_session(user_id, session_data)
                return {"text": response_text, "keyboard": "0||00"}
            except psycopg2.DatabaseError as e:
                logging.error(f"❌ خطأ أثناء حذف جميع التذكيرات لـ {user_id}: {e}")
                response_text = "❌ حدث خطأ أثناء حذف التنبيهات.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                return {"text": response_text, "keyboard": "0||00"}
            finally:
                if not conn:
                    close_db_connection(conn)
        elif message == "1":
            session_data["state"] = "set_reminder_type"
            session_data["history"] = history + [current_state]
            session_data["reminder_type"] = "موعد مستشفى أو مناسبة"
            set_session(user_id, session_data)
            response_text = (
                "📅 الرجاء إدخال تاريخ التذكير (أمثلة: 2025-07-16، 16-07-2025، 07/16/2025):\n\n"
                "⏰ الوقت (أمثلة: 14:30، 02:30 PM، 2:30):\n\n"
                "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
            )
            return {"text": response_text, "keyboard": "0||00"}
        elif message == "2":
            session_data["state"] = "set_reminder_type"
            session_data["history"] = history + [current_state]
            session_data["reminder_type"] = "تذكير بأكل الدواء"
            set_session(user_id, session_data)
            response_text = (
                "📅 الرجاء إدخال تاريخ التذكير (أمثلة: 2025-07-16، 16-07-2025، 07/16/2025):\n\n"
                "⏰ الوقت (أمثلة: 14:30، 02:30 PM، 2:30):\n\n"
                "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
            )
            return {"text": response_text, "keyboard": "0||00"}
        elif message == "3":
            session_data["state"] = "set_reminder_type"
            session_data["history"] = history + [current_state]
            session_data["reminder_type"] = "منبه أذكار الصباح والمساء"
            set_session(user_id, session_data)
            response_text = (
                "📅 الرجاء إدخال تاريخ التذكير (أمثلة: 2025-07-16، 16-07-2025، 07/16/2025):\n\n"
                "⏰ الوقت (أمثلة: 14:30، 02:30 PM، 2:30):\n\n"
                "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
            )
            return {"text": response_text, "keyboard": "0||00"}
        elif message == "4":
            try:
                c = conn.cursor()
                c.execute('SELECT id, reminder_type, message, remind_at, interval_days FROM reminders WHERE user_id = %s AND active = TRUE', (user_id,))
                reminders = c.fetchall()
                if not reminders:
                    response_text = "📭 لا توجد تنبيهات نشطة.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                    return {"text": response_text, "keyboard": "0||00"}
                response_text = "📜 *تنبيهاتي الحالية*:\n\n"
                for i, reminder in enumerate(reminders, 1):
                    reminder_id, reminder_type, msg, remind_at, interval_days = reminder
                    remind_at_str = remind_at.astimezone(pytz.timezone("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M")
                    response_text += f"{i}. {reminder_type}: {msg} (🕒 {remind_at_str}) {'🔄 كل ' + str(interval_days) + ' أيام' if interval_days > 0 else ''}\n"
                response_text += "\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                return {"text": response_text, "keyboard": "0||00"}
            except psycopg2.DatabaseError as e:
                logging.error(f"❌ خطأ أثناء جلب التنبيهات لـ {user_id}: {e}")
                response_text = "❌ حدث خطأ أثناء جلب التنبيهات.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                return {"text": response_text, "keyboard": "0||00"}
            finally:
                if not conn:
                    close_db_connection(conn)
        elif message == "5":
            try:
                c = conn.cursor()
                c.execute('SELECT reminders_sent FROM reminder_stats WHERE user_id = %s', (user_id,))
                stats = c.fetchone()
                reminders_sent = stats[0] if stats else 0
                response_text = (
                    f"📊 *إحصائياتي* 📊\n\nعدد التنبيهات المرسلة: {reminders_sent}\n\n"
                    "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                )
                return {"text": response_text, "keyboard": "0||00"}
            except psycopg2.DatabaseError as e:
                logging.error(f"❌ خطأ أثناء جلب الإحصائيات لـ {user_id}: {e}")
                response_text = "❌ حدث خطأ أثناء جلب الإحصائيات.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                return {"text": response_text, "keyboard": "0||00"}
            finally:
                if not conn:
                    close_db_connection(conn)
        response_text = (
            "⏰ *منبه* ⏰\n\nاختر نوع التذكير الذي تريده:\n\n1️⃣ موعد مستشفى أو مناسبة 🩺\n"
            "2️⃣ تذكير بأكل الدواء 💊\n3️⃣ منبه أذكار الصباح والمساء 📿\n4️⃣ تنبيهاتي الحالية 📜\n"
            "5️⃣ إحصائياتي 📊\n\n❌ لحذف جميع التنبيهات أرسل: حذف\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)"
        )
        return {"text": response_text, "keyboard": "1||2||3||4||5||حذف||0"}
    
    elif current_state == "set_reminder_type":
        date_time_match = re.match(r"(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})\s*(\d{1,2}:[\d:]{2}\s*(AM|PM)?)?", message)
        if date_time_match:
            date_str = date_time_match.group(1)
            time_str = date_time_match.group(2) or "00:00"
            
            parsed_date = parse_date(date_str)
            if not parsed_date:
                response_text = (
                    "❌ تنسيق التاريخ غير صحيح. استخدم أحد التنسيقات التالية:\n"
                    "- 2025-07-16\n- 16-07-2025\n- 07/16/2025\n\n"
                    "⏰ الوقت (أمثلة: 14:30، 02:30 PM، 2:30):\n\n"
                    "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                )
                return {"text": response_text, "keyboard": "0||00"}
            
            parsed_time = parse_time(time_str)
            if not parsed_time:
                response_text = (
                    "❌ تنسيق الوقت غير صحيح. استخدم أحد التنسيقات التالية:\n"
                    "- 14:30\n- 02:30 PM\n- 2:30\n\n"
                    "📅 التاريخ (أمثلة: 2025-07-16، 16-07-2025، 07/16/2025):\n\n"
                    "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                )
                return {"text": response_text, "keyboard": "0||00"}
            
            remind_at = parsed_date.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            session_data["remind_at"] = remind_at
            session_data["state"] = "set_reminder_message"
            session_data["history"] = history + [current_state]
            set_session(user_id, session_data)
            response_text = "📝 الرجاء إدخال رسالة التذكير:\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
            return {"text": response_text, "keyboard": "0||00"}
        
        response_text = (
            "📅 الرجاء إدخال تاريخ التذكير (أمثلة: 2025-07-16، 16-07-2025، 07/16/2025):\n\n"
            "⏰ الوقت (أمثلة: 14:30، 02:30 PM، 2:30) - يمكن إدخاله مع التاريخ (مثل 2025-07-16 14:30):\n\n"
            "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
        )
        return {"text": response_text, "keyboard": "0||00"}
    
    elif current_state == "set_reminder_message":
        session_data["message"] = message
        session_data["state"] = "set_reminder_interval"
        session_data["history"] = history + [current_state]
        set_session(user_id, session_data)
        response_text = (
            "🔄 هل تريد تكرار التذكير؟\n\n1️⃣ بدون تكرار\n2️⃣ يوميًا\n3️⃣ أسبوعيًا\n4️⃣ شهريًا\n\n"
            "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
        )
        return {"text": response_text, "keyboard": "1||2||3||4||0||00"}
    
    elif current_state == "set_reminder_interval":
        interval_map = {"1": 0, "2": 1, "3": 7, "4": 30}
        if message in interval_map:
            interval_days = interval_map[message]
            try:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO reminders (user_id, reminder_type, message, remind_at, interval_days)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, session_data["reminder_type"], session_data["message"], 
                      session_data["remind_at"], interval_days))
                conn.commit()
                response_text = (
                    "✅ *تم إنشاء التذكير بنجاح!* 🎉\n\n📌 نوع التذكير: {session_data['reminder_type']}\n"
                    f"💬 الرسالة: {session_data['message']}\n"
                    f"🕒 الوقت: {session_data['remind_at'].astimezone(pytz.timezone('Asia/Riyadh')).strftime('%Y-%m-%d %H:%M')}\n"
                    f"🔄 التكرار: {'بدون تكرار' if interval_days == 0 else 'كل ' + str(interval_days) + ' أيام'}\n\n"
                    "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                )
                session_data = {"state": "reminder_menu", "history": history}
                set_session(user_id, session_data)
                return {"text": response_text, "keyboard": "0||00"}
            except psycopg2.DatabaseError as e:
                logging.error(f"❌ خطأ أثناء إنشاء تذكير لـ {user_id}: {e}")
                response_text = "❌ حدث خطأ أثناء إنشاء التذكير.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                return {"text": response_text, "keyboard": "0||00"}
            finally:
                if not conn:
                    close_db_connection(conn)
        response_text = (
            "🔄 هل تريد تكرار التذكير؟\n\n1️⃣ بدون تكرار\n2️⃣ يوميًا\n3️⃣ أسبوعيًا\n4️⃣ شهريًا\n\n"
            "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
        )
        return {"text": response_text, "keyboard": "1||2||3||4||0||00"}
    
    elif current_state.startswith("service_"):
        service = current_state.replace("service_", "")
        categories = get_categories()
        if service == "صيدلية":
            pharmacies = [cat for cat in categories if "pharmacy" in cat.get("code", "").lower()]
            try:
                idx = int(message) - 1
                if 0 <= idx < len(pharmacies):
                    pharmacy = pharmacies[idx]
                    response_text = (
                        f"🏥 *{pharmacy.get('name')}* 💊\n\n{pharmacy.get('description', 'لا توجد تفاصيل متاحة')}\n"
                        f"⏰ *أوقات العمل:*\n  🌅 صباحًا: {pharmacy.get('morning_start_time', 'غير متوفر')} - {pharmacy.get('morning_end_time', 'غير متوفر')}\n"
                        f"  🌙 مساءً: {pharmacy.get('evening_start_time', 'غير متوفر')} - {pharmacy.get('evening_end_time', 'غير متوفر')}\n\n"
                        "↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
                    )
                    return {"text": response_text, "keyboard": "0||00"}
            except ValueError:
                pass
            return display_category_list(user_id, service, pharmacies, session_data)
        response_text = f"⚙️ الخدمة '{service}' قيد التطوير.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)\n🔙 للرجوع إلى القائمة السابقة اضغط 00"
        return {"text": response_text, "keyboard": "0||00"}
    
    if not conn and conn is not None:
        close_db_connection(conn)
    return {"text": "❌ حالة غير معروفة. يرجى المحاولة مرة أخرى.\n\n↩️ للرجوع للقائمة 🏠 الرئيسية (0)", "keyboard": "0"}
