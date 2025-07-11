import logging
from flask import Flask, request, jsonify
import os
import requests

# استيرادات الخدمات
from services.governmental import handle_government_services
from services.pharmacies   import handle as handle_pharmacies
from services.grocery      import handle as handle_grocery
from services.restaurants  import handle as handle_restaurants
from services.shops        import handle as handle_shops
from services.chalets      import handle as handle_chalets
from services.sand         import handle as handle_sand
from services.shovel       import handle as handle_shovel
from services.butchers     import handle as handle_butchers
from services.home_businesses   import handle as handle_home_businesses
from services.building_materials import handle as handle_building_materials

from services.reminder import (
    handle as handle_reminder,
    get_session,               # لاختبار وجود جلسة نشطة
)

from send_reminders import send_due_reminders

# إعداد Flask
app = Flask(__name__)

# بيانات UltraMsg
INSTANCE_ID = "instance130542"
TOKEN       = "pr2bhaor2vevcrts"
API_URL     = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# رسائل ثابتة
greetings      = ["سلام", "السلام", "السلام عليكم", "السلام عليكم ورحمة الله"]
menu_triggers  = ["0", "٠", "صفر", ".", "القائمة", "خدمات", "المنيو", "نقطة", "نقطه"]

menu_message = """
*_أهلا بك في دليل خدمات القرين يمكنك الإستعلام عن الخدمات التالية:_*

1️⃣ حكومي🏢  
2️⃣ صيدلية💊  
3️⃣ بقالة🥤  
4️⃣ خضار🥬  
5️⃣ رحلات⛺️  
6️⃣ حلا🍮  
7️⃣ أسر منتجة🥧  
8️⃣ مطاعم🍔  
9️⃣ قرطاسية📗  
🔟 محلات 🏪
----
11- شالية
12- وايت
13- شيول
14- دفان
15- مواد بناء وعوازل
16- عمال
17- متاجر
18- ذبائح وملاحم
19- نقل مدرسي ومشاوير
20- منبه ⏰

📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*
"""

# ---------- Webhook ----------
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(force=True)
    sender  = payload.get("sender")          # تأكد من مفتاح JSON الصحيح
    message = payload.get("message", "").strip()

    if not sender or not message:
        return jsonify({"success": False}), 200

    normalized = message.replace("ـ", "").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").lower()

    # 1️⃣ جلسة منبه نشطة؟ -> أعطها الأولوية
    if get_session(sender) or normalized in {"20", "٢٠", "منبه", "منبّه", "تذكير", "توقف"}:
        reply = handle_reminder(message, sender)

    # 2️⃣ التحيات والقائمة
    elif normalized in greetings:
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"
    elif normalized in menu_triggers:
        reply = menu_message

    # 3️⃣ الخدمات الرئيسية (لا تصلها الأرقام إذا كان المستخدم داخل جلسة)
    elif normalized in {"1", "١", "حكومي"}:
        reply = handle_government_services(message, sender)
    elif normalized in {"2", "٢", "صيدلية"}:
        reply = handle_pharmacies(message, sender)
    elif normalized in {"3", "٣", "بقالة"}:
        reply = handle_grocery(message, sender)
    elif normalized in {"8", "٨", "مطاعم"}:
        reply = handle_restaurants(message, sender)
    elif normalized in {"10", "١٠", "محلات"}:
        reply = handle_shops(message, sender)
    elif normalized in {"11", "١١", "شالية"}:
        reply = handle_chalets(message, sender)
    elif normalized in {"14", "١٤", "دفان"}:
        reply = handle_sand(message, sender)
    elif normalized in {"13", "١٣", "شيول"}:
        reply = handle_shovel(message, sender)
    elif normalized in {"18", "١٨", "ذبائح", "لحوم", "ملحمة"}:
        reply = handle_butchers(message, sender)
    elif normalized in {"7", "٧", "أسر منتجة"}:
        reply = handle_home_businesses(message, sender)
    elif normalized in {"15", "١٥", "مواد بناء", "عوازل"}:
        reply = handle_building_materials(message, sender)
    else:
        reply = "🤖 عذراً، لم أفهم طلبك. أرسل 0 لعرض القائمة الرئيسية."

    # إرسال الرد عبر UltraMsg
    requests.post(API_URL, data={
        "token": TOKEN,
        "to": sender,
        "body": reply
    })

    return jsonify({"success": True}), 200

# ---------- Route كرون لتشغيل التذكيرات ----------
@app.route("/run-reminders", methods=["GET"])
def run_reminders():
    send_due_reminders()
    return jsonify({"status": "Reminders sent"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
