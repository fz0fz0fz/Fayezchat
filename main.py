from flask import Flask, request, jsonify
import requests, os

# استيراد جميع الخدمات كدوال مباشرة
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
    reminder  # الجديد
)

app = Flask(__name__)

# بيانات UltraMsg
INSTANCE_ID = "instance130542"
TOKEN       = "pr2bhaor2vevcrts"
API_URL     = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# خريطة الأرقام والكلمات للخدمات (بدون .handle)
services_map = {
    "1":  governmental,
    "2":  pharmacies,
    "3":  grocery,
    "4":  vegetables,
    "5":  trips,
    "6":  desserts,
    "7":  home_businesses,
    "8":  restaurants,
    "9":  stationery,
    "10": shops,
    "11": chalets,
    "12": water,
    "13": shovel,
    "14": sand,
    "15": building_materials,
    "16": workers,
    "17": stores,
    "18": butchers,
    "19": school_transport,
    "20": reminder,
    "منبه": reminder,
    "منبّه": reminder,
    "تذكير": reminder,
}

# كلمات التحية
greetings = [
    "سلام", "السلام", "السلام عليكم", "السلام عليكم ورحمة الله"
]

# الكلمات التي تعرض القائمة
menu_triggers = ["0", "٠", "صفر", ".", "القائمة", "خدمات", "نقطة", "نقطه"]

# نص القائمة
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

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    sender = data.get("data", {}).get("from")
    msg = data.get("data", {}).get("body", "").strip()

    if not sender or not msg:
        return jsonify({"success": False}), 200

    normalized = msg.strip().replace("ـ", "").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").lower()

    if normalized in greetings:
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"

    elif normalized in menu_triggers:
        reply = menu_message

    elif normalized in services_map:
        try:
            reply = services_map[normalized](msg, sender)
        except TypeError:
            reply = services_map[normalized](msg)

    else:
        reply = "🤖 عذراً، لم أفهم طلبك. أرسل 0 لعرض القائمة الرئيسية."

    requests.post(API_URL, data={
        "token": TOKEN,
        "to": sender,
        "body": reply
    })

    return jsonify({"success": True}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
