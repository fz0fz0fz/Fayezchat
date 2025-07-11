from flask import Flask, request, jsonify
import requests, os

# استيراد جميع الخدمات
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

INSTANCE_ID = "instance130542"
TOKEN       = "pr2bhaor2vevcrts"
API_URL     = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

services_map = {
    "1":  governmental.handle,
    "2":  pharmacies.handle,
    "3":  grocery.handle,
    "4":  vegetables.handle,
    "5":  trips.handle,
    "6":  desserts.handle,
    "7":  home_businesses.handle,
    "8":  restaurants.handle,
    "9":  stationery.handle,
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
    "20": alarm.handle,           # ← المنبّه
}

ARABIC2LATIN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
greetings      = ["سلام","السلام","السلام عليكم","السلام عليكم ورحمة الله"]
menu_triggers  = ["0","٠","صفر",".","القائمة","خدمات","نقطة","نقطه"]
menu_message = "... (رسالة القائمة كما كانت) ..."

def normalize(txt: str) -> str:
    txt = txt.strip().lower()
    txt = (txt.replace("ـ","")
             .replace("أ","ا").replace("إ","ا").replace("آ","ا")
             .translate(ARABIC2LATIN))
    return txt

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(force=True).get("data", {})
    sender  = payload.get("from")
    body    = payload.get("body", "")

    if not sender or not body:
        return jsonify({"success": False}), 200

    normalized = normalize(body)
    first_word = normalized.split()[0] if normalized.split() else ""

    # 1) خدمة مخصّصة بالأولوية
    handler = None
    if first_word in services_map:
        handler = services_map[first_word]
    elif normalized in services_map:
        handler = services_map[normalized]

    if handler:
        # نحاول تمـرير sender إن كانت الدالة تقبل برقمين:
        try:
            reply = handler(body, sender)        # مثال alarm.handle(msg, user)
        except TypeError:
            reply = handler(body)                # بقية الخدمات تقبل msg واحد
    elif normalized in greetings:
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"
    elif normalized in menu_triggers:
        reply = menu_message
    else:
        reply = "🤖 عذراً، لم أفهم طلبك. أرسل 0 لعرض القائمة الرئيسية."

    requests.post(API_URL, data={
        "token": TOKEN,
        "to": sender,
        "body": reply,
        "priority": 10
    })
    return jsonify({"success": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
