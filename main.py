from flask import Flask, request, jsonify
import requests, os

# --- استيراد الخدمات ---
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
    water_truck,
    shovel,
    sand,
    building_materials,
    workers,
    stores,
    butchers,
    transport,
    alarm
)

app = Flask(__name__)

# بيانات UltraMsg
INSTANCE_ID = "instance130542"
TOKEN       = "pr2bhaor2vevcrts"
API_URL     = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# خريطة رقم/كلمة ↦ دالة الخدمة
SERVICE_DISPATCH = {
    "1": governmental.handle,      "حكومي": governmental.handle,
    "2": pharmacies.handle,        "صيدلية": pharmacies.handle,
    "3": grocery.handle,           "بقالة": grocery.handle,
    "4": vegetables.handle,        "خضار": vegetables.handle,
    "5": trips.handle,             "رحلات": trips.handle,
    "6": desserts.handle,          "حلا": desserts.handle,
    "7": home_businesses.handle,   "أسر": home_businesses.handle,
    "8": restaurants.handle,       "مطاعم": restaurants.handle,
    "9": stationery.handle,        "قرطاسية": stationery.handle,
    "10": shops.handle,            "محلات": shops.handle,
    "11": chalets.handle,          "شالية": chalets.handle,
    "12": water_truck.handle,      "وايت": water_truck.handle,
    "13": shovel.handle,           "شيول": shovel.handle,
    "14": sand.handle,             "دفان": sand.handle,
    "15": building_materials.handle,"مواد": building_materials.handle,
    "16": workers.handle,          "عمال": workers.handle,
    "17": stores.handle,           "متاجر": stores.handle,
    "18": butchers.handle,         "ذبائح": butchers.handle,
    "19": transport.handle,        "نقل": transport.handle,
    "20": alarm.handle,            "منبه": alarm.handle,
}

# التحيات
greetings = [
    "سلام", "سلام عليكم", "السلام", "سلام عليكم ورحمة الله",
    "سلام عليكم ورحمة الله وبركاته", "سلااام", "السلاام",
    "سلاآم", "سسلام", "السلامم", "السسلآم"
]

# كلمات تُظهر القائمة
menu_triggers = ["٠", ".", "0", "صفر", "نقطة", "نقطه",
                 "خدمات", "القائمة", "خدمات القرين", "الخدمات"]

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
17- محلات
18- ذبائح وملاحم
19- نقل مدرسي ومشاوير
20- منبه ⏰

📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*
"""

# عداد الرسائل غير المفهومة
unknown_count = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.get_json(force=True)

    payload = event.get("data", {})
    sender  = payload.get("from")
    message = (payload.get("body") or "").strip().lower()

    if not sender or not message:
        return jsonify({"success": False, "error": "No message"}), 200

    normalized = (message.replace("ـ", "")
                           .replace("أ", "ا")
                           .replace("آ", "ا")
                           .replace("إ", "ا"))

    # التحيات
    if any(greet in normalized for greet in greetings):
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"

    # القائمة
    elif any(trg in normalized for trg in menu_triggers):
        reply = menu_message

    # خدمات محددة
    else:
        handler = SERVICE_DISPATCH.get(normalized) or SERVICE_DISPATCH.get(normalized.split()[0])
        if handler:
            reply = handler(message)
            unknown_count.pop(sender, None)
        else:
            cnt = unknown_count.get(sender, 0) + 1
            unknown_count[sender] = cnt
            if cnt < 3:
                reply = "🤖 عذراً، لم أفهم طلبك. أرسل صفر (0) لعرض القائمة الرئيسية"
            else:
                reply = ("🤖 عذراً، لم أفهم طلبك تم تحويل رسالتك "
                         "وسيتم الرد عليك في أقرب وقت")
                forward_to_admin(sender, message)

    send_whatsapp(sender, reply)
    return jsonify({"success": True}), 200


def send_whatsapp(to, body):
    requests.post(
        API_URL,
        data={
            "token": TOKEN,
            "to": to,
            "body": body,
            "priority": 10
        },
        timeout=10
    )


def forward_to_admin(sender, original):
    admin = "966503813344"
    txt   = f"📨 رسالة غير مفهومة من {sender}:\n\n{original}"
    send_whatsapp(admin, txt)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
