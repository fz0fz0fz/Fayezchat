import psycopg2
import os
import json
import logging

# تهيئة السجل (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# الحصول على DATABASE_URL من متغيرات البيئة (لاستخدام PostgreSQL)
DB_URL = os.getenv("DATABASE_URL")

def init_session_db():
    """
    تهيئة جدول الجلسات في قاعدة البيانات PostgreSQL إن لم يكن موجودًا.
    """
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

# استدعاء التهيئة عند تحميل الملف
init_session_db()

def get_session(user_id: str) -> dict:
    """
    جلب حالة الجلسة للمستخدم من قاعدة البيانات PostgreSQL.
    يُرجع قاموسًا إذا وجدت الجلسة، أو قاموسًا فارغًا إذا لم يكن هناك جلسة.
    """
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set in environment variables.")
        return {}

    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT state FROM sessions WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}  # إرجاع قاموس فارغ إذا لم تكن هناك جلسة
    except Exception as e:
        logging.error(f"❌ خطأ أثناء جلب الجلسة لـ {user_id}: {e}")
        return {}
    finally:
        if conn is not None:
            conn.close()

def set_session(user_id: str, state: dict):
    """
    حفظ حالة الجلسة للمستخدم في قاعدة البيانات PostgreSQL.
    إذا كان state فارغًا، يتم حذف الجلسة.
    """
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set in environment variables.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        if not state:  # إذا كان القاموس فارغًا، احذف الجلسة
            cursor.execute('DELETE FROM sessions WHERE user_id = %s', (user_id,))
        else:
            state_json = json.dumps(state)
            cursor.execute('INSERT INTO sessions (user_id, state) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET state = %s', 
                           (user_id, state_json, state_json))
        conn.commit()
    except Exception as e:
        logging.error(f"❌ خطأ أثناء حفظ الجلسة لـ {user_id}: {e}")
    finally:
        if conn is not None:
            conn.close()
