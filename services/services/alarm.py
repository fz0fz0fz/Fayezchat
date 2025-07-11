from datetime import datetime, timedelta

# ذاكرة مؤقتة لتخزين حالة المستخدمين
pending_users = {}

def handle(msg: str, user_number=None) -> str:
    text = msg.strip()

    if user_number in pending_users:
        state = pending_users[user_number]

        # الرد على اختيار مدة التذكير بتغيير الزيت
        if state["step"] == "oil_change_waiting_duration":
            del pending_users[user_number]

            duration_map = {
                "1": 30,
                "2": 60,
                "3": 90
            }

            days = duration_map.get(text)
            if not days:
                return "❌ خيار غير صحيح. أرسل 1 أو 2 أو 3 فقط."

            target_date = datetime.now() + timedelta(days=days)
            return f"✅ تم حفظ تذكير تغيير الزيت بعد {days} يوم.\n📆 سنذكّرك في {target_date.strftime('%Y-%m-%d')}"

    if text in ["منبه", "20", "٢٠"]:
        return (
            "*🔔 خدمة المنبه - اختر ما تود التذكير به:*\n\n"
            "1️⃣ تغيير الزيت\n"
            "2️⃣ موعد مستشفى أو مناسبة\n"
            "3️⃣ تذكير استغفار\n"
            "4️⃣ تذكير الصلاة على النبي ﷺ يوم الجمعة\n"
            "5️⃣ تذكير بأخذ الدواء\n\n"
            "🛑 أرسل 'توقف' لإيقاف أي تنبيهات مفعّلة."
        )

    if text == "1":
        pending_users[user_number] = {
            "step": "oil_change_waiting_duration"
        }
        return (
            "🛢️ *كل كم تود أن نذكّرك بتغيير الزيت؟*\n"
            "1️⃣ بعد شهر\n"
            "2️⃣ بعد شهرين\n"
            "3️⃣ بعد 3 أشهر"
        )

    return "❌ خيار غير مفهوم ضمن خدمة المنبه."
