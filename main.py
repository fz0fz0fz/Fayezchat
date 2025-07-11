from flask import Flask, request, jsonify
import requests, os

# --- استيراد جميع الخدمات ---
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
    water_truck,        # <-- الاسم الصحيح
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

# --- أداة تطبيع النص -------------------------------------------------
AR2LAT = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
def normalize(txt: str) -> str:
    return (txt.strip()
               .replace("ـ", "")
               .replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
               .translate(AR2LAT)
               .lower())

# --- خريطة الأرقام والكلمات ↦ دوال الخدمات ---------------------------
services_map = {
    # أضفنا المفاتيح بالأرقام العربية أيضاً
    "1": governmental.handle,   "١": governmental.handle,
    "2": pharmacies.handle,     "٢": pharmacies.handle,
    "3": grocery.handle,        "٣": grocery.handle,
    "4": vegetables.handle,     "٤": vegetables.handle,
    "5": trips.handle,          "٥": trips.handle,
    "6": desserts.handle,       "٦": desserts.handle,
    "7": home_businesses.handle,"٧": home_businesses.handle,
    "8": restaurants.handle,    "٨": restaurants.handle,
    "9": stationery.handle,     "٩": stationery.handle,
    "10": shops.handle,         "١٠": shops.handle,
    "11": chalets.handle,       "١١": chalets.handle,
    "12": water_truck.handle,   "١٢": water_truck.handle,
    "13": shovel.handle,        "١٣": shovel.handle,
    "14": sand.handle,          "١٤": sand.handle,
    "15": building_materials.handle, "١٥": building_materials.handle,
    "16": workers.handle,       "١٦": workers.handle,
    "17": stores.handle,        "١٧": stores.handle,
    "18": butchers.handle,      "١٨": butchers.handle,
    "19": school_transport.handle, "١٩": school_transport.handle,
    "20": alarm.handle,         "٢٠": alarm.handle,
    "منبه": alarm.handle, "منبّه": alarm.handle,
}

# التحيات والكلمات التي تظهر القائمة
greetings = {
    "سلام", "السلام", "السلام عليكم", "السلام عليكم ورحمة الله"
}
menu_triggers = {"0", "٠", "صفر", ".", "القائمة", "خدمات", "نقطة", "نقطه"}

menu_message = """(نفس نص القائمة كما هو)"""

# ------------------------- Webhook ----------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data   = request.get_json(force=True)
    sender = data.get("data", {}).get("from")   # رقم العميل
    raw    = data.get("data", {}).get("body", "")

    if not sender or not raw:
        return jsonify(success=False), 200

    msg = normalize(raw)

    # تحيّة
    if msg in greetings:
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"

    # القائمة
    elif msg in menu_triggers:
        reply = menu_message

    # خدمات
    elif msg in services_map:
        service = services_map[msg]
        try:
            reply = service(raw, sender)   # يمرّر رقم المستخدم للخدمات التي تحتاجه
        except TypeError:
            reply = service(raw)           # خدمات لا تحتاج الرقم

    else:
        reply = "🤖 عذراً، لم أفهم طلبك. أرسل 0 لعرض القائمة الرئيسية."

    # إرسال الرد
    requests.post(API_URL, data={
        "token": TOKEN,
        "to": sender,
        "body": reply
    }, timeout=10)

    return jsonify(success=True), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
