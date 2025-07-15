import psycopg2
import os
import json
import logging
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# تهيئة السجل
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# الحصول على DATABASE_URL
DB_URL = os.getenv("DATABASE_URL")

def init_session_db():
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set in environment variables.")
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT PRIMARY KEY,
                state TEXT
            )
        ''')
        conn.commit()
        logging.info("✅ تم إنشاء جدول sessions في قاعدة البيانات PostgreSQL إن لم يكن موجودًا.")
    except Exception as e:
        logging.error(f"❌ خطأ أثناء تهيئة جدول sessions: {e}")
    finally:
        if conn is not None:
            conn.close()
            logging.info("🔒 Database connection closed during session table initialization")

init_session_db()

def get_session(user_id: str) -> dict:
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set in environment variables.")
        return {"state": "main_menu", "history": []}
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT state FROM sessions WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        if row and row[0]:
            state = json.loads(row[0])
            if "history" not in state:
                state["history"] = []
            return state
        return {"state": "main_menu", "history": []}
    except (psycopg2.DatabaseError, json.JSONDecodeError) as e:
        logging.error(f"❌ خطأ أثناء جلب الجلسة لـ {user_id}: {e}")
        return {"state": "main_menu", "history": []}
    finally:
        if conn is not None:
            conn.close()

def set_session(user_id: str, state: dict):
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set in environment variables.")
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        if not state:
            cursor.execute('DELETE FROM sessions WHERE user_id = %s', (user_id,))
        else:
            state_json = json.dumps(state)
            cursor.execute('INSERT INTO sessions (user_id, state) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET state = %s', 
                           (user_id, state_json, state_json))
        conn.commit()
    except psycopg2.DatabaseError as e:
        logging.error(f"❌ خطأ أثناء حفظ الجلسة لـ {user_id}: {e}")
    finally:
        if conn is not None:
            conn.close()
