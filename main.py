# main.py (نسخة اختبارية)

import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "OK", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    # استلام البيانات كما هي
    data = request.get_json(force=True, silent=True) or {}

    # طباعة البيانات في اللوق لرؤيتها في Render
    print("🚨 البيانات المستلَمة من UltraMsg:", data, flush=True)

    # استخراج الحقول (قد تختلف الأسماء؛ سنعرفها بعد الطباعة)
    sender  = data.get("sender")
    message = data.get("message")

    # ردّ إيكو بسيط للتأكّد أنّ كل شيء يعمل
    return jsonify({
        "reply": f"📨 وصلتنا رسالتك: {message}"
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
