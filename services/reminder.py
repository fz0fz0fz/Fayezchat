def handle(msg: str, sender: str) -> dict:
    session = get_session(sender)
    text = msg.strip()

    if text == "0":
        set_session(sender, None)
        return {"reply": MAIN_MENU_TEXT}

    if text == "00":
        if session and "last_menu" in session:
            last_menu = session["last_menu"]
            set_session(sender, {"menu": last_menu, "last_menu": "main"})
            return handle(last_menu, sender)
        else:
            return {"reply": MAIN_MENU_TEXT}

    if text == "حذف":
        return delete_all_reminders(sender)

    if session is None:
        if text == "20":
            set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
            return {"reply": REMINDER_MENU_TEXT}
        else:
            return {"reply": MAIN_MENU_TEXT}

    if session.get("menu") == "reminder_main":
        if text == "2":
            set_session(sender, {"menu": "reminder_date", "last_menu": "reminder_main"})
            return {
                "reply": (
                    "📅 أرسل تاريخ الموعد بالميلادي فقط :\n"
                    "مثل: 17-08-2025\n"
                    "وسيتم تذكيرك قبل الموعد بيوم واحد\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }
        elif text == "6":
            return list_user_reminders(sender)
        else:
            return {"reply": "↩️ اختر رقم صحيح أو 'توقف'."}

    if session.get("menu") == "reminder_date":
        try:
            parts = [int(p) for p in re.split(r"[-./_\\\s]+", text.strip()) if p]
            if len(parts) == 3:
                day, month, year = parts
                if year < 100: year += 2000
                date_obj = datetime(year, month, day)
                remind_at = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                save_reminder(sender, "hospital", None, remind_at)
                set_session(sender, {"menu": "reminder_main", "last_menu": "main"})
                return {
                    "reply": f"✅ تم ضبط التذكير، سيتم التذكير بتاريخ {remind_at}\n\n↩️ للرجوع (00) | 🏠 رئيسية (0)"
                }
            else:
                raise ValueError
        except:
            return {
                "reply": (
                    "❗️صيغة غير صحيحة. أرسل التاريخ مثل: 17-08-2025\n\n"
                    "↩️ للرجوع (00) | 🏠 رئيسية (0)"
                )
            }

    return {"reply": MAIN_MENU_TEXT}
