from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# بيانات UltraMsg
INSTANCE_ID = "instance131412"
TOKEN = "whjwn3rfyo6r9n48"
API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

# ذاكرة لتتبع المحاولات
unknown_count = {}

# قائمة التحيات المقبولة (مع بعض الأخطاء الشائعة)
greetings = [
    "سلام", "سلام عليكم", "السلام", "سلام عليكم ورحمة الله", "سلام عليكم ورحمة الله وبركاته",
    "سلااام", "السلاام", "سلاآم", "سسلام", "السلامم", "السسلآم"
]

# كلمات القائمة
menu_triggers = ["٠", ".", "0", "صفر", "نقطة", "نقطه", "خدمات", "القائمة", "خدمات القرين", "الخدمات"]

# الرد على القائمة
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
11-  شالية 
12- وايت 
13- شيول
14-دفان
15- مواد بناء وعوازل
16- عمال
17- محلات 
18- ذبائح وملاحم
19- نقل مدرسي ومشاوير 

📝 *أرسل رقم أو اسم الخدمة مباشرة لعرض التفاصيل.*
"""

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    sender = data.get("body", {}).get("from")
    message = data.get("body", {}).get("text", "").strip().lower()

    if not sender or not message:
        return jsonify({"success": False, "error": "No message found"})

    response_text = ""
    normalized_msg = message.replace("ـ", "").replace("أ", "ا").replace("آ", "ا").replace("إ", "ا")

    if any(greet in normalized_msg for greet in greetings):
        response_text = "وعليكم السلام ورحمة الله وبركاته 👋"

    elif any(trigger in normalized_msg for trigger in menu_triggers):
        response_text = menu_message

    else:
        # سجل عدد المرات غير المفهومة لهذا المستخدم
        count = unknown_count.get(sender, 0) + 1
        unknown_count[sender] = count

        if count < 3:
            response_text = "🤖 عذراً، لم أفهم طلبك. أرسل صفر (0) لعرض القائمة الرئيسية"
        else:
            response_text = "🤖 عذراً، لم أفهم طلبك تم تحويل رسالتك وسيتم الرد عليك في أقرب وقت"
            forward_message_to_admin(sender, message)

    send_whatsapp_message(sender, response_text)
    return jsonify({"success": True})


def send_whatsapp_message(to, message):
    data = {
        "token": TOKEN,
        "to": to,
        "body": message,
        "priority": 10,
        "referenceId": ""
    }
    requests.post(API_URL, data=data)


def forward_message_to_admin(sender, original_message):
    admin_number = "966503813344"
    forward_text = f"📨 رسالة غير مفهومة من {sender}:\n\n{original_message}"
    send_whatsapp_message(admin_number, forward_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
