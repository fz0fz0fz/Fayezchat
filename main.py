@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}

    sender = (data.get("sender") or "").strip()
    message = (data.get("message") or "").strip()

    if not sender or not message:
        return jsonify({"reply": "حدث خطأ في البيانات المستلمة."})

    # 🔁 جلسة المنبه إذا كانت فعالة
    session = get_session(sender)
    if session and session.startswith("reminder"):
        reply = handle_reminder(message, sender)
        return jsonify({"reply": reply})

    # ✅ رسالة العودة للقائمة الرئيسية
    if message in ["0", "رجوع", "عودة", "القائمة"]:
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

    # الخدمات حسب الرسائل
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
    elif message in ["20", "منبه", "تذكير", "منبّه"]:
        reply = handle_reminder(message, sender)
        return jsonify({"reply": reply})

    # رد افتراضي
    return jsonify({"reply": "مرحبًا! أرسل رقم الخدمة أو اسمها للحصول على التفاصيل."})
