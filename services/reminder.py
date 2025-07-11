... بقية الوارد كما هو ↑↑

def handle(msg: str, sender: str) -> str: text = msg.strip().lower()

# إيقاف كل التنبيهات
if text == "توقف":
    conn = sqlite3.connect(REMINDERS_DB)
    c = conn.cursor()
    c.execute("UPDATE reminders SET active = 0 WHERE sender = ?", (sender,))
    conn.commit()
    conn.close()
    set_session(sender, None)
    return "🛑 تم إيقاف جميع التنبيهات بنجاح."

# احصل على حالة الجلسة
session_state = get_session(sender)

# ====== الخطوة ❶ : القائمة الرئيسـية للمنبّه ======
if text in {"20", "٢٠", "منبه", "منبّه", "تذكير"}:
    # نحفظ أننا داخل قائمة المنبّه
    set_session(sender, "reminder_menu")
    return (
        "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
        "1️⃣ تغيير الزيت\n"
        "2️⃣ موعد مستشفى أو مناسبة\n"
        "3️⃣ تذكير استغفار\n"
        "4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة\n"
        "5️⃣ تذكير بأخذ الدواء\n\n"
        "🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة."
    )

# ====== الخطوة ❷ : اختيار عنصر من القائمة ======
if session_state == "reminder_menu":
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
        return "↩️ أرسل 1 أو 3 لاختيار نوع التذكير، أو 'توقف' للخروج."

# ====== متابعة خطوات تغيير الزيت ======
if session_state == "oil_change_waiting_duration":
    if text in {"1", "2", "3"}:
        months = int(text)
        remind_at = datetime.now() + timedelta(days=30 * months)
        conn = sqlite3.connect(REMINDERS_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO reminders (sender, type, remind_at) VALUES (?,?,?)",
            (sender, "تغيير الزيت", remind_at.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        set_session(sender, None)
        return f"✅ تم ضبط تذكير تغيير الزيت بعد {months} شهر."
    return "📌 اختر 1 = شهر، 2 = شهرين، 3 = 3 أشهر."

# ====== متابعة خطوات الاستغفار ======
if session_state == "istighfar_waiting_interval":
    interval_map = {"1": 30, "2": 60, "3": 120}
    if text in interval_map:
        minutes = interval_map[text]
        next_time = datetime.now() + timedelta(minutes=minutes)
        conn = sqlite3.connect(REMINDERS_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO reminders (sender, type, interval_minutes, remind_at) VALUES (?,?,?,?)",
            (sender, "استغفار", minutes, next_time.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        set_session(sender, None)
        return f"✅ تم ضبط تذكير الاستغفار كل {minutes} دقيقة."
    return "📌 اختر: 1 = كل 30 دقيقة، 2 = كل ساعة، 3 = كل ساعتين."

# ====== في حال طلب غير مفهوم ======
return "🤖 لم أفهم طلبك في خدمة المنبه. أرسل 'منبه' لعرض القائمة أو 'توقف' لإلغاء التنبيهات."

