from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# بيانات UltraMsg
INSTANCE_ID = "instance130542"
TOKEN       = "pr2bhaor2vevcrts"
API_URL     = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# ذاكرة لعدّ الرسائل غير المفهومة
unknown_count = {}

# التحيات
greetings = [
    "سلام", "سلام عليكم", "السلام", "سلام عليكم ورحمة الله",
    "سلام عليكم ورحمة الله وبركاته", "سلااام", "السلاام",
    "سلاآم", "سسلام", "السلامم", "السسلآم"
]

# كلمات تُظهر القائمة
menu_triggers = ["٠", ".", "0", "صفر", "نقطة", "نقطه",
                 "خدمات", "القائمة", "خدمات القرين", "الخدمات"]

# نص القائمة
menu_message = """
*_أهلا بك في دليل خدمات القرين يمكنك الإستعلام عن الخدمات التالية:_*

1️⃣ حكومي🏢  
2️⃣ صيدلية💊  
3️⃣ بقالة🥤  
4️⃣ خضار🥬  
5️⃣ رحلات⛺️  
6️⃣ حلا🍮  
7️⃣ أسر منتجة🥧  
8️⃣ مطاعم🍔  
9️⃣ قرطاسية📗  
🔟 محلات 🏪
----
11- شالية
12- وايت
13- شيول
14- دفان
15- مواد بناء وعوازل
16- عمال
17- محلات
18- ذبائح وملاحم
19- نقل مدرسي ومشاوير

📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*
"""

@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.get_json(force=True)

    # UltraMsg يضع الرسالة هنا: event["data"]["body"]
    payload = event.get("data", {})
    sender  = payload.get("from")
    message = (payload.get("body") or "").strip().lower()

    if not sender or not message:
        return jsonify({"success": False, "error": "No message"}), 200

    normalized = (message.replace("ـ", "")
                           .replace("أ", "ا")
                           .replace("آ", "ا")
                           .replace("إ", "ا"))

    # تحديد الردّ
    if any(greet in normalized for greet in greetings):
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"

    elif any(trg in normalized for trg in menu_triggers):
        reply = menu_message

    else:
        cnt = unknown_count.get(sender, 0) + 1
        unknown_count[sender] = cnt
        if cnt < 3:
            reply = "🤖 عذراً، لم أفهم طلبك. أرسل صفر (0) لعرض القائمة الرئيسية"
        else:
            reply = ("🤖 عذراً، لم أفهم طلبك تم تحويل رسالتك "
                     "وسيتم الرد عليك في أقرب وقت")
            forward_to_admin(sender, message)

    send_whatsapp(sender, reply)
    return jsonify({"success": True}), 200


def send_whatsapp(to, body):
    requests.post(
        API_URL,
        data={
            "token": TOKEN,
            "to": to,
            "body": body,
            "priority": 10
        },
        timeout=10
    )


def forward_to_admin(sender, original):
    admin = "966503813344"
    txt   = f"📨 رسالة غير مفهومة من {sender}:\n\n{original}"
    send_whatsapp(admin, txt)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # يدعم Render
    app.run(host="0.0.0.0", port=port)
