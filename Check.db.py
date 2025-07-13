# Check.db.py
import sqlite3
import os
import logging

# تهيئة السجل (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# مسارات قواعد البيانات المستخدمة في المشروع
REMINDERS_DB_PATH = "reminders.db"
SESSIONS_DB_PATH = "sessions.db"
SERVICES_DB_PATH = "services.db"

def check_and_init_databases():
    """
    التحقق من وجود قواعد البيانات المطلوبة وإنشائها إن لم تكن موجودة.
    """
    try:
        # التحقق من reminders.db (للتذكيرات)
        if not os.path.exists(REMINDERS_DB_PATH):
            conn = sqlite3.connect(REMINDERS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    message TEXT,
                    remind_at TEXT NOT NULL,
                    interval_days INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1
                )
            ''')
            conn.commit()
            logging.info(f"✅ تم إنشاء قاعدة البيانات {REMINDERS_DB_PATH}.")
            conn.close()
        else:
            logging.info(f"🟢 قاعدة البيانات {REMINDERS_DB_PATH} موجودة بالفعل.")

        # التحقق من sessions.db (للجلسات)
        if not os.path.exists(SESSIONS_DB_PATH):
            conn = sqlite3.connect(SESSIONS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT PRIMARY KEY,
                    state TEXT
                )
            ''')
            conn.commit()
            logging.info(f"✅ تم إنشاء قاعدة البيانات {SESSIONS_DB_PATH}.")
            conn.close()
        else:
            logging.info(f"🟢 قاعدة البيانات {SESSIONS_DB_PATH} موجودة بالفعل.")

        # التحقق من services.db (للخدمات مثل الصيدليات)
        if not os.path.exists(SERVICES_DB_PATH):
            conn = sqlite3.connect(SERVICES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    morning_start_time TEXT,
                    morning_end_time TEXT,
                    evening_start_time TEXT,
                    evening_end_time TEXT
                )
            ''')
            conn.commit()
            logging.info(f"✅ تم إنشاء قاعدة البيانات {SERVICES_DB_PATH}.")
            conn.close()
        else:
            logging.info(f"🟢 قاعدة البيانات {SERVICES_DB_PATH} موجودة بالفعل.")

        return True
    except Exception as e:
        logging.error(f"❌ خطأ أثناء التحقق من قواعد البيانات: {e}")
        return False

if __name__ == "__main__":
    if check_and_init_databases():
        print("✅ جميع قواعد البيانات جاهزة للاستخدام.")
    else:
        print("❌ حدث خطأ أثناء التحقق من قواعد البيانات.")
