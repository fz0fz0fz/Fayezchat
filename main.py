import logging
import os
from flask import Flask, request, jsonify

# === استيراد الخدمات الفرعية ===
from services.pharmacies import handle as handle_pharmacies
from services.grocery import handle as handle_grocery
from services.restaurants import handle as handle_restaurants
from services.shops import handle as handle_shops
from services.chalets import handle as handle_chalets
from services.sand import handle as handle_sand
from services.shovel import handle as handle_shovel
from services.butchers import handle as handle_butchers
from services.home_businesses import handle as handle_home_businesses
from services.building_materials import handle as handle_building_materials
from services.governmental import handle as handle_government_services

# منبّه (الدوالتين معاً)
from services.reminder import handle as handle_reminder, get_session

# === تهيئة فلاسـك ===
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ---------- أداة توحيد الإرجاع ----------
def make_reply(resp):
    """
    بعض الـ handlers تُعيد dict جاهز، وبعضها تُعيد نصًّا فقط.
    هذه الدالة توحّد الاستجابة إلى JSON مطابق لتنسيق WhatsApp API.
    """
    if isinstance(resp, dict):
        return jsonify(resp)
    return jsonify({"reply": str(resp)})


# ---------- المسارات ----------
@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Bot is running."


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}

    sender  = (data.get("sender")  or "").strip()
    message = (data.get("message") or "").strip()

    if not sender or not message:
        return make_reply("🚫 بيانات غير صالحة.")

    # ↩️ لو كان في جلسة منبّه نشطة
    session = get_session(sender)
    if session and session.startswith("reminder"):
        return make_reply(handle_reminder(message, sender))

    # ---------- القائمة الرئيسية ----------
    if message in {"0", "رجوع", "عودة", "القائمة"}:
        return make_reply(
            "*أهلا بك في دليل خدمات القرين*\n"
            "يمكنك الإستعلام عن الخدمات التالية:\n\n"
            "1️⃣ حكومي🏢\n"
            "2️⃣ صيدلية💊\n"
            "3️⃣ بقالة🥤\n"
            "4️⃣ خضار🥬\n"
            "5️⃣ رحلات⛺️\n"
            "6️⃣ حلا🍮\n"
            "7️⃣ أسر منتجة🥧\n"
            "8️⃣ مطاعم🍔\n"
            "9️⃣ قرطاسية📗\n"
            "🔟 محلات 🏪\n"
            "11️⃣ شالية\n"
            "12️⃣ وايت\n"
            "13️⃣ شيول\n"
            "14️⃣ دفان\n"
            "15️⃣ مواد بناء وعوازل\n"
            "16️⃣ عمال\n"
            "17️⃣ محلات\n"
            "18️⃣ ذبائح وملاحم\n"
            "19️⃣ نقل مدرسي ومشاوير\n"
            "20️⃣ منبه📆"
        )

    # ---------- توجيه حسب الرقم ----------
    if message in {"1", "حكومي"}:
        return make_reply(handle_government_services(message, sender))
    if message in {"2", "صيدلية"}:
        return make_reply(handle_pharmacies(message, sender))
    if message in {"3", "بقالة"}:
        return make_reply(handle_grocery(message, sender))
    if message in {"8", "مطاعم"}:
        return make_reply(handle_restaurants(message, sender))
    if message in {"10", "محلات"}:
        return make_reply(handle_shops(message, sender))
    if message in {"11", "شالية"}:
        return make_reply(handle_chalets(message, sender))
    if message in {"14", "دفان"}:
        return make_reply(handle_sand(message, sender))
    if message in {"13", "شيول"}:
        return make_reply(handle_shovel(message, sender))
    if message in {"18", "ذبائح", "لحوم", "ملحمة"}:
        return make_reply(handle_butchers(message, sender))
    if message in {"7", "أسر منتجة"}:
        return make_reply(handle_home_businesses(message, sender))
    if message in {"15", "مواد بناء", "عوازل"}:
        return make_reply(handle_building_materials(message, sender))
    if message in {"20", "منبه", "تذكير", "منبّه"}:
        return make_reply(handle_reminder(message, sender))

    # ---------- رد افتراضي ----------
    return make_reply("🤖 لم أفهم طلبك، أرسل رقم الخدمة أو اسمها.")


# ---------- تشغيل محلي ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
