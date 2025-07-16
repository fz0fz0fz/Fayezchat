from typing import Dict, List
import psycopg2
import os
from .session import get_session, set_session
from .db import get_categories
from .db_pool import get_db_connection, close_db_connection
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
            "16. عمال 👷\n17. محلات مهنية 🔨\n18. ذبائح وملاحم 🥩\n19. نقل مدرسي ومشاوير 🚍\n\n"
            "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
        )
        keyboard = "1||2||3||4||5||6||7||8||9||10||11||12||13||14||15||16||17||18||19"
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
                "16. عمال 👷\n17. محلات مهنية 🔨\n18. ذبائح وملاحم 🥩\n19. نقل مدرسي ومشاوير 🚍\n\n"
                "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
            )
            keyboard = "1||2||3||4||5||6||7||8||9||10||11||12||13||14||15||16||17||18||19"
            return {"text": response_text, "keyboard": keyboard}
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
            "16": "عمال", "17": "محلات مهنية", "18": "ذبائح وملاحم", "19": "نقل مدرسي ومشاوير"
        }
        service_names = {v: k for k, v in services.items()}
        selected_service = services.get(message) or service_names.get(message.lower())

        if selected_service:
            if selected_service == "صيدلية":
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
            "16. عمال 👷\n17. محلات مهنية 🔨\n18. ذبائح وملاحم 🥩\n19. نقل مدرسي ومشاوير 🚍\n\n"
            "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
        )
        keyboard = "1||2||3||4||5||6||7||8||9||10||11||12||13||14||15||16||17||18||19"
        return {"text": response_text, "keyboard": keyboard}

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
