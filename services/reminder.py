def handle(msg: str, sender: str) -> str:
    text = msg.strip().lower()

    # 🔙 الرجوع للقائمة الرئيسية
    if text == "0":
        set_session(sender, None)
        return "🔙 تم الرجوع للقائمة الرئيسية.\n\nأرسل رقم الخدمة أو اسمها للحصول على التفاصيل."

    # 🛑 إيقاف التنبيهات
    if text == "توقف":
        conn = sqlite3.connect(REMINDERS_DB)
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
        conn.commit()
        conn.close()
        set_session(sender, None)
        return "🛑 تم إيقاف جميع التنبيهات بنجاح."

    session = get_session(sender)

    # ========== ❶ فتح القائمة الرئيسية لخدمة المنبه ==========
    if text in {"20", "٢٠", "منبه", "منبّه", "تذكير"}:
        set_session(sender, "reminder_menu")
        return (
            "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
            "1️⃣ تغيير الزيت\n"
            "2️⃣ موعد مستشفى أو مناسبة\n"
            "3️⃣ تذكير استغفار\n"
            "4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة\n"
            "5️⃣ تذكير بأخذ الدواء\n\n"
            "🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة.\n"
            "0️⃣ للرجوع إلى القائمة الرئيسية."
        )

    # ========== ❷ اختيار أحد عناصر المنبه ==========
    if session == "reminder_menu":
        if text == "1":
            set_session(sender, "oil_change_waiting_duration")
            return (
                "🛢️ *كم المدة التي ترغب أن نذكرك بعدها لتغيير الزيت؟*\n\n"
                "1️⃣ شهر\n"
                "2️⃣ شهرين\n"
                "3️⃣ 3 أشهر"
            )
        elif text == "3":
            set_session(sender, "istighfar_waiting_interval")
            return (
                "🧎‍♂️ *كم مرة ترغب بالتذكير بالاستغفار؟*\n\n"
                "1️⃣ كل نصف ساعة\n"
                "2️⃣ كل ساعة\n"
                "3️⃣ كل ساعتين"
            )
        else:
            return "↩️ أرسل رقم صحيح لاختيار نوع التذكير أو 'توقف' للخروج."

    # ========== ❸ ضبط تغيير الزيت ==========
    if session == "oil_change_waiting_duration":
        if text in {"1", "2", "3"}:
            months = int(text)
            remind_at = datetime.now() + timedelta(days=30 * months)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender, type, remind_at) VALUES (?, ?, ?)",
                (sender, "تغيير الزيت", remind_at.strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            set_session(sender, None)
            return f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."
        return "📌 اختر: 1 = شهر، 2 = شهرين، 3 = 3 أشهر."

    # ========== ❹ ضبط تذكير الاستغفار ==========
    if session == "istighfar_waiting_interval":
        interval_map = {"1": 30, "2": 60, "3": 120}
        if text in interval_map:
            minutes = interval_map[text]
            next_time = datetime.now() + timedelta(minutes=minutes)
            conn = sqlite3.connect(REMINDERS_DB)
            c = conn.cursor()
            c.execute(
                "INSERT INTO reminders (sender, type, interval_minutes, remind_at) VALUES (?, ?, ?, ?)",
                (sender, "استغفار", minutes, next_time.strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            set_session(sender, None)
            return f"✅ تم ضبط تذكير الاستغفار كل {minutes} دقيقة."
        return "📌 اختر: 1 = كل 30 دقيقة، 2 = كل ساعة، 3 = كل ساعتين."

    # ========== الرد الافتراضي ==========
    return "🤖 لم أفهم طلبك في خدمة المنبه. أرسل 'منبه' لعرض القائمة أو 'توقف' لإلغاء التنبيهات."
