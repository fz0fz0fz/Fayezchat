import logging from flask import Flask, request, jsonify import os

استيراد الخدمات

from services.pharmacies import handle as handle_pharmacies from services.grocery import handle as handle_grocery from services.restaurants import handle as handle_restaurants from services.shops import handle as handle_shops from services.chalets import handle as handle_chalets from services.sand import handle as handle_sand from services.shovel import handle as handle_shovel from services.butchers import handle as handle_butchers from services.home_businesses import handle as handle_home_businesses from services.reminder import handle as handle_reminder, get_session from services.building_materials import handle as handle_building_materials from services.governmental import handle as handle_governmental

app = Flask(name)

@app.route("/", methods=["GET"]) def home(): return "WhatsApp Bot is running."

@app.route("/webhook", methods=["POST"]) def webhook(): data = request.get_json() sender = data.get("sender") message = data.get("message") if message: message = message.strip() else: return jsonify({"reply": "❗️الرسالة غير صالحة أو فارغة."})

# 🔁 إذا كان المستخدم داخل جلسة منبه → لا تذهب لأي خدمة ثانية
session = get_session(sender)
if session and session.startswith("reminder"):
    return handle_reminder(message, sender)

# الخدمات حسب الرسائل
if message in ["1", "حكومي"]:
    return handle_governmental(message, sender)
elif message in ["2", "صيدلية"]:
    return handle_pharmacies(message, sender)
elif message in ["3", "بقالة"]:
    return handle_grocery(message, sender)
elif message in ["8", "مطاعم"]:
    return handle_restaurants(message, sender)
elif message in ["10", "محلات"]:
    return handle_shops(message, sender)
elif message in ["11", "شالية"]:
    return handle_chalets(message, sender)
elif message in ["14", "دفان"]:
    return handle_sand(message, sender)
elif message in ["13", "شيول"]:
    return handle_shovel(message, sender)
elif message in ["18", "ذبائح", "لحوم", "ملحمة"]:
    return handle_butchers(message, sender)
elif message in ["7", "أسر منتجة"]:
    return handle_home_businesses(message, sender)
elif message in ["15", "مواد بناء", "عوازل"]:
    return handle_building_materials(message, sender)
elif message in ["20", "منبه", "تذكير", "منبّه"]:
    return handle_reminder(message, sender)

# رد افتراضي
return jsonify({"reply": "مرحبًا! أرسل رقم الخدمة أو اسمها للحصول على التفاصيل."})

if name == "main": app.run(debug=True)

