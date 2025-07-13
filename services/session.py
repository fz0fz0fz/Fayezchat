# services/session.py
import sqlite3
import os
import json

# مسار قاعدة البيانات للجلسات
SESSION_DB_PATH = os.path.join(os.getcwd(), "sessions.db")

# تهيئة قاعدة البيانات
def init_session_db():
    try:
        conn = sqlite3.connect(SESSION_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT PRIMARY KEY,
                state TEXT
            )
        ''')
        conn.commit()
        print("✅ تم إنشاء قاعدة البيانات sessions.db إن لم تكن موجودة.")
    except Exception as e:
        print(f"❌ خطأ أثناء إنشاء قاعدة البيانات sessions.db: {e}")
    finally:
        conn.close()

# استدعاء التهيئة عند تحميل الملف
init_session_db()

def get_session(user_id):
    """
    جلب حالة الجلسة للمستخدم من قاعدة البيانات.
    """
    try:
        conn = sqlite3.connect(SESSION_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT state FROM sessions WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return None
    except Exception as e:
        print(f"❌ خطأ أثناء جلب الجلسة لـ {user_id}: {e}")
        return None
    finally:
        conn.close()

def set_session(user_id, state):
    """
    حفظ حالة الجلسة للمستخدم في قاعدة البيانات.
    إذا كان state فارغًا، يتم حذف الجلسة.
    """
    try:
        conn = sqlite3.connect(SESSION_DB_PATH)
        cursor = conn.cursor()
        if state is None:
            cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
        else:
            state_json = json.dumps(state)
            cursor.execute('INSERT OR REPLACE INTO sessions (user_id, state) VALUES (?, ?)', 
                           (user_id, state_json))
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ أثناء حفظ الجلسة لـ {user_id}: {e}")
    finally:
        conn.close()
