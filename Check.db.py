import os

db_path = os.path.join(os.getcwd(), "reminders.db")

if os.path.exists(db_path):
    print("✅ قاعدة البيانات reminders.db موجودة.")
else:
    print("❌ قاعدة البيانات reminders.db غير موجودة.")
