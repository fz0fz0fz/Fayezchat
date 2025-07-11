import logging
from flask import Flask, request, jsonify
import os
import sqlite3
from datetime import datetime, timedelta

# استيراد الخدمات
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

app = Flask(__name__)

# قواعد البيانات
REMINDERS_DB = "reminders.db"
sessions = {}

def get_session(user_id):
    return sessions.get(user_id)

def set_session(user_id, value):
    sessions[user_id] = value

def clear_session(user_id):
    sessions.pop(user_id, None)

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    sender = (data.get("sender") or "").strip()
    message = (data.get("message") or "").strip()

    if not sender or not message:
        return jsonify({"reply": "حدث خطأ في البيانات المستلمة."})

    # الرجوع للقائمة الرئيسية
    if message in ["0", "رجوع", "عودة", "القائمة"]:
        clear_session(sender)
        return jsonify({
            "reply": (
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
                "11- شالية\n"
                "12- وايت\n"
                "13- شيول\n"
                "14- دفان\n"
                "15- مواد بناء وعوازل\n"
                "16- عمال\n"
                "17- محلات\n"
                "18- ذبائح وملاحم\n"
                "19- نقل مدرسي ومشاوير\n"
                "20- منبه📆"
            )
        })

    session = get_session(sender)

    # إيقاف التنبيهات
    if message == "توقف":
        conn = sqlite3.connect(REMINDERS_DB)
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        conn.commit()
        conn.close()
        clear_session(sender)
        return jsonify({"reply": "🛑 تم إيقاف جميع التنبيهات بنجاح."})

    # قائمة المنبه
    if message in {"20", "٢٠", "منبه", "منبّه", "تذكير"}:
        set_session(sender, "reminder_menu")
        return jsonify({"reply":
            "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
            "1️⃣ تغيير الزيت\n"
            "2️⃣ موعد مستشفى أو مناسبة\n"
            "3️⃣ تذكير استغفار\n"
            "4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة\n"
            "5️⃣ تذكير بأخذ الدواء\n\n"
            "🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة.\n"
            "0️⃣ للرجوع إلى القائمة الرئيسية."
        })

    if session == "reminder_menu":
        if message == "1":
            set_session(sender, "oil_change_waiting_duration")
            return jsonify({"reply":
                "🛢️ *كم المدة التي ترغب أن نذكرك بعدها لتغيير الزيت؟*\n\n"
                "1️⃣ شهر\n"
                "2️⃣ شهرين\n"
                "3️⃣ 3 أشهر"
            })
        elif message == "3":
            set_session(sender, "istighfar_waiting_interval")
            return jsonify({"reply":
                "🧎‍♂️ *كم مرة ترغب بالتذكير بالاستغفار؟*\n\n"
                "1️⃣ كل نصف ساعة\n"
                "2️⃣ كل ساعة\n"
                "3️⃣ كل ساعتين"
            })
        else:
            return jsonify({"reply": "↩️ أرسل رقم صحيح لاختيار نوع التذكير أو 'توقف' للخروج."})

    if session == "oil_change_waiting_duration":
        if message in {"1", "2", "3"}:
            months = int(message)
            remind_at = datetime.now() + timedelta(days=30 * months)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender, type, remind_at) VALUES (?, ?, ?)",
                (sender, "تغيير الزيت", remind_at.strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            clear_session(sender)
            return jsonify({"reply": f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."})
        return jsonify({"reply": "📌 اختر: 1 = شهر، 2 = شهرين، 3 = 3 أشهر."})

    if session == "istighfar_waiting_interval":
        interval_map = {"1": 30, "2": 60, "3": 120}
        if message in interval_map:
            minutes = interval_map[message]
            next_time = datetime.now() + timedelta(minutes=minutes)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender, type, interval_minutes, remind_at) VALUES (?, ?, ?, ?)",
                (sender, "استغفار", minutes, next_time.strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            clear_session(sender)
            return jsonify({"reply": f"✅ تم ضبط تذكير الاستغفار كل {minutes} دقيقة."})
        return jsonify({"reply": "📌 اختر: 1 = كل 30 دقيقة، 2 = كل ساعة، 3 = كل ساعتين."})

    # الخدمات الأخرى
    if message in ["1", "حكومي"]:
        return handle_government_services(message, sender)
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

    # رد افتراضي
    return jsonify({"reply": "🤖 أرسل رقم الخدمة أو اسمها للحصول على التفاصيل."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
