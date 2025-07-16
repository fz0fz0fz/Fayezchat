from typing import Dict, List
import logging
from .session import get_session, set_session
from .db import get_categories
from services.db_pool import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def display_category_list(user_id: str, service: str, categories: List[Dict], session_data: Dict) -> Dict[str, str]:
    session_data["state"] = f"service_{service}"
    session_data["history"] = session_data.get("history", []) + [session_data.get("state", "main_menu")]
    set_session(user_id, session_data)
    if not categories:
        response_text = f"❌ لا توجد بيانات متاحة لـ {service}.\n\n🔙 اضغط 0 للقائمة الرئيسية."
        return {"text": response_text, "keyboard": "0"}
    response_text = f"📌 قائمة {service}:\nاختر رقم:\n\n"
    keyboard_items = []
    for i, category in enumerate(categories, 1):
        response_text += f"{i}. {category.get('emoji', '📌')} {category.get('name', 'غير معروف')}\n"
        keyboard_items.append(f"{i}")
    response_text += "\n🔙 0 للقائمة الرئيسية | 00 للسابق"
    keyboard = "||".join(keyboard_items) + "||0||00" if keyboard_items else "0||00"
    return {"text": response_text, "keyboard": keyboard}

def handle_reminder(user_id: str, message: str, conn=None) -> Dict[str, str]:
    if not conn:
        conn = get_db_connection()
        if not conn:
            return {"text": "❌ فشل الاتصال بقاعدة البيانات.\n\n0 للقائمة الرئيسية", "keyboard": "0"}

    session_data = get_session(user_id)
    current_state = session_data.get("state", "main_menu")
    history = session_data.get("history", [])

    if message == "0":
        session_data = {"state": "main_menu", "history": []}
        set_session(user_id, session_data)
        return main_menu_response()

    if message == "00" and history:
        previous_state = history.pop()
        session_data = {"state": previous_state, "history": history}
        set_session(user_id, session_data)
        if previous_state == "main_menu":
            return main_menu_response()
        elif previous_state.startswith("service_"):
            service = previous_state.replace("service_", "")
            categories = get_categories_for_service(service)
            return display_category_list(user_id, service, categories, session_data)

    if current_state == "main_menu":
        services = {
            "1": "حكومي", "حكومي": "حكومي",
            "2": "صيدلية", "صيدلية": "صيدلية",
            "3": "بقالة", "بقالة": "بقالة",
            "4": "خضار", "خضار": "خضار",
            "5": "رحلات", "رحلات": "رحلات",
            "6": "حلا", "حلا": "حلا",
            "7": "أسر منتجة", "أسر منتجة": "أسر منتجة",
            "8": "مطاعم", "مطاعم": "مطاعم",
            "9": "قرطاسية", "قرطاسية": "قرطاسية",
            "10": "محلات", "محلات": "محلات",
            "11": "شالية", "شالية": "شالية",
            "12": "وايت", "وايت": "وايت",
            "13": "شيول", "شيول": "شيول",
            "14": "دفان", "دفان": "دفان",
            "15": "مواد بناء وعوازل", "مواد بناء وعوازل": "مواد بناء وعوازل",
            "16": "عمال", "عمال": "عمال",
            "17": "محلات مهنية", "محلات مهنية": "محلات مهنية",
            "18": "ذبائح وملاحم", "ذبائح وملاحم": "ذبائح وملاحم",
            "19": "نقل مدرسي ومشاوير", "نقل مدرسي ومشاوير": "نقل مدرسي ومشاوير",
            "20": "منبه", "منبه": "منبه",
        }
        selected_service = services.get(message)
        if selected_service:
            categories = get_categories_for_service(selected_service)
            if categories:  # إذا كانت هناك بيانات (مثل صيدلية)
                return display_category_list(user_id, selected_service, categories, session_data)
            else:  # خدمات قيد التطوير
                session_data["state"] = f"service_{selected_service}"
                session_data["history"] = history + [current_state]
                set_session(user_id, session_data)
                response_text = f"⚙️ الخدمة '{selected_service}' قيد التطوير.\n\n🔙 0 للقائمة الرئيسية | 00 للسابق"
                return {"text": response_text, "keyboard": "0||00"}
        # إذا كان الإدخال غير صالح، أعد عرض القائمة
        return main_menu_response(error="❌ اختيار غير صالح. جرب رقم أو اسم خدمة.")

    elif current_state.startswith("service_"):
        service = current_state.replace("service_", "")
        categories = get_categories_for_service(service)
        try:
            idx = int(message) - 1
            if 0 <= idx < len(categories):
                cat = categories[idx]
                response_text = (
                    f"{cat.get('emoji')} *{cat.get('name')}*\n\n{cat.get('description', 'لا تفاصيل')}\n"
                    f"⏰ صباحًا: {cat.get('morning_start_time', 'غير متوفر')} - {cat.get('morning_end_time', 'غير متوفر')}\n"
                    f"مساءً: {cat.get('evening_start_time', 'غير متوفر')} - {cat.get('evening_end_time', 'غير متوفر')}\n\n"
                    "🔙 0 للقائمة الرئيسية | 00 للسابق"
                )
                return {"text": response_text, "keyboard": "0||00"}
            else:
                # رقم غير صالح في السياق الفرعي، أعد عرض القائمة
                return display_category_list(user_id, service, categories, session_data)
        except ValueError:
            # إذا لم يكن رقمًا، أعد عرض القائمة
            return display_category_list(user_id, service, categories, session_data)

    return {"text": "❌ حالة غير معروفة.\n\n0 للقائمة الرئيسية", "keyboard": "0"}

def main_menu_response(error: str = ""):
    response_text = (
        f"{error}\n" if error else "" +
        "🌟 *أهلا بك في دليل خدمات القرين يمكنك الإستعلام عن الخدمات التالية:* 🌟\n\n"
        "1️⃣ حكومي 🏢\n2️⃣ صيدلية 💊\n3️⃣ بقالة 🥤\n4️⃣ خضار 🥬\n5️⃣ رحلات ⛺️\n"
        "6️⃣ حلا 🍮\n7️⃣ أسر منتجة 🥧\n8️⃣ مطاعم 🍔\n9️⃣ قرطاسية 📗\n🔟 محلات 🏪\n"
        "----\n11. شالية 🏖\n12. وايت 🚛\n13. شيول 🚜\n14. دفان 🏗\n15. مواد بناء وعوازل 🧱\n"
        "16. عمال 👷\n17. محلات مهنية 🔨\n18. ذبائح وملاحم 🥩\n19. نقل مدرسي ومشاوير 🚍\n20. منبه ⏰\n\n"
        "📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*"
    )
    keyboard = "1||2||3||4||5||6||7||8||9||10||11||12||13||14||15||16||17||18||19||20"
    return {"text": response_text, "keyboard": keyboard}

def get_categories_for_service(service):
    categories = get_categories()
    return [cat for cat in categories if service.lower() in cat.get("code", "").lower() or service.lower() in cat.get("name", "").lower()]
