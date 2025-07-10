from flask import Flask, request, jsonify
import requests, os
import logging

# تهيئة الـ logging للتشخيص
logging.basicConfig(level=logging.DEBUG)

# استيراد كل الخدمات
from services import (
    governmental,
    pharmacies,
    grocery,
    vegetables,
    trips,
    desserts,
    home_businesses,
    restaurants,
    stationery,
    shops,
    chalets,
    water,
    shovel,
    sand,
    building_materials,
    workers,
    stores,
    butchers,
    school_transport,
    alarm
)

app = Flask(__name__)

# بيانات UltraMsg
INSTANCE_ID = "instance130542"
TOKEN       = "pr2bhaor2vevcrts"
API_URL     = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# خريطة الأرقام للخدمات
services_map = {
    "1": governmental.handle,
    "2": pharmacies.handle,
    "3": grocery.handle,
    "4": vegetables.handle,
    "5": trips.handle,
    "6": desserts.handle,
    "7": home_businesses.handle,
    "8": restaurants.handle,
    "9": stationery.handle,
    "10": shops.handle,
    "11": chalets.handle,
    "12": water.handle,
    "13": shovel.handle,
    "14": sand.handle,
    "15": building_materials.handle,
    "16": workers.handle,
    "17": stores.handle,
    "18": butchers.handle,
    "19": school_transport.handle,
    "20": alarm.handle,
}

# تحيات والقائمة
greetings = ["سلام", "السلام", "السلام عليكم", "السلام عليكم ورحمة الله"]
menu_triggers = ["0", "٠", "صفر", ".", "القائمة", "خدمات", "نقطة", "نقطه"]
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

# تحويل الأرقام العربية إلى لاتينية
ARABIC2LATIN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

@app.route("/webhook", methods=["POST"])
def webhook():
    data   = request.get_json(force=True)
    sender = data.get("data", {}).get("from")
    msg    = data.get("data", {}).get("body", "")

    if not sender or not msg:
        return jsonify({"success": False}), 200

    # تطبيع النص وتحويل الأرقام
    normalized = (
        msg.strip()
           .replace("ـ", "")
           .replace("أ", "ا")
           .replace("إ", "ا")
           .replace("آ", "ا")
           .translate(ARABIC2LATIN)
           .lower()
    )

    # طباعة للتشخيص
    logging.debug(f"[DEBUG] raw msg: '{msg}' → normalized: '{normalized}'")

    # محاولة إيجاد معالج الخدمة
    handler = None
    if normalized in services_map:
        handler = services_map[normalized]
    else:
        # جرّب أول “توكن” بعد إزالة علامات ترقيم
        token = normalized.split()[0].rstrip(".,!?")
        if token in services_map:
            handler = services_map[token]

    # بناء الرد
    if handler:
        reply = handler(msg)
    elif normalized in greetings:
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"
    elif normalized in menu_triggers:
        reply = menu_message
    else:
        reply = "🤖 عذراً، لم أفهم طلبك. أرسل 0 لعرض القائمة الرئيسية."

    # إرسال الرد عبر UltraMsg
    requests.post(
        API_URL,
        data={
            "token": TOKEN,
            "to": sender,
            "body": reply
        },
        timeout=10
    )

    return jsonify({"success": True}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
