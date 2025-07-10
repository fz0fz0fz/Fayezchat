from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# بيانات UltraMsg
INSTANCE_ID = "instance131412"
TOKEN = "whjwn3rfyo6r9n48"
API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# ذاكرة لتتبع المحاولات غير المفهومة
unknown_count = {}

# التحيات (مع أخطاء شائعة)
greetings = [
    "سلام", "سلام عليكم", "السلام", "سلام عليكم ورحمة الله",
    "سلام عليكم ورحمة الله وبركاته", "سلااام", "السلاام",
    "سلاآم", "سسلام", "السلامم", "السسلآم"
]

# كلمات تُشغّل القائمة
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
    data = request.get_json(force=True)
    sender  = data.get("body", {}).get("from")
    message = data.get("body", {}).get("text", "").strip().lower()

    if not sender or not message:
        return jsonify({"success": False, "error": "Empty payload"})

    # تنعيم النص (إزالة همزات، مدّات …)
    normalized = (message.replace("ـ", "")
                           .replace("أ", "ا")
                           .replace("آ", "ا")
                           .replace("إ", "ا"))

    # اختيار الرد المناسب
    if any(greet in normalized for greet in greetings):
        reply = "وعليكم السلام ورحمة الله وبركاته 👋"

    elif any(trigger in normalized for trigger in menu_triggers):
        reply = menu_message

    else:
        # زيادة عدّاد الرسائل غير المفهومة
        count = unknown_count.get(sender, 0) + 1
        unknown_count[sender] = count

        if count < 3:
            reply = "🤖 عذراً، لم أفهم طلبك. أرسل صفر (0) لعرض القائمة الرئيسية"
        else:
            reply = ("🤖 عذراً، لم أفهم طلبك تم تحويل رسالتك "
                     "وسيتم الرد عليك في أقرب وقت")
            forward_to_admin(sender, message)

    send_whatsapp(sender, reply)
    return jsonify({"success": True})


def send_whatsapp(to, body):
    data = {
        "token": TOKEN,
        "to": to,
        "body": body,
        "priority": 10
    }
    requests.post(API_URL, data=data, timeout=10)


def forward_to_admin(sender, original):
    admin = "966503813344"
    text  = f"📨 رسالة غير مفهومة من {sender}:\n\n{original}"
    send_whatsapp(admin, text)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # <-- هذا هو التعديل المهم
    app.run(host="0.0.0.0", port=port)
