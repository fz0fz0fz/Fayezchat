import psycopg2
import os
import logging
from .db_pool import get_db_connection, close_db_connection  # استيراد الدوال الجديدة
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def init_db_and_insert_data():
    conn = get_db_connection()
    if not conn:
        logging.error("❌ DATABASE_URL not set in environment variables or connection failed.")
        return
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                morning_start_time TIME,
                morning_end_time TIME,
                evening_start_time TIME,
                evening_end_time TIME,
                emoji TEXT DEFAULT '💊'
            )
        ''')
        c.execute("DELETE FROM categories")
        data = [
            (
                "صيدلية١", "صيدلية ركن أطلس (القرين)", 
                "📞 0556945390\n📱 واتس اب\n📍 الموقع: https://maps.app.goo.gl/KGDcPGwvuym1E8YFA\n🚚 خدمة التوصيل: نعم",
                "08:00", "12:00", "16:00", "23:00", "💊"
            ),
            (
                "صيدلية٢", "صيدلية دواء القصيم",
                "📞 0500000000\n📍 الموقع: https://maps.app.goo.gl/test",
                "08:30", "12:30", "16:30", "23:30", "💊"
            ),
        ]
        c.executemany('''
            INSERT INTO categories (code, name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time, emoji)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                morning_start_time = EXCLUDED.morning_start_time,
                morning_end_time = EXCLUDED.morning_end_time,
                evening_start_time = EXCLUDED.evening_start_time,
                evening_end_time = EXCLUDED.evening_end_time,
                emoji = EXCLUDED.emoji
        ''', data)
        conn.commit()
        logging.info("✅ تم تهيئة جدول categories وإدخال البيانات الافتراضية.")
    except psycopg2.DatabaseError as e:
        logging.error(f"❌ خطأ أثناء تهيئة قاعدة البيانات: {e}")
    finally:
        close_db_connection(conn)
        logging.info("🔒 Database connection closed for init_db_and_insert_data")

def get_categories():
    conn = get_db_connection()
    if not conn:
        logging.error("❌ DATABASE_URL not set in environment variables or connection failed.")
        return []
    try:
        c = conn.cursor()
        c.execute('SELECT code, name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time, emoji FROM categories')
        categories = c.fetchall()
        result = []
        for cat in categories:
            code, name, desc, m_start, m_end, e_start, e_end, emoji = cat
            result.append({
                "code": code,
                "name": name,
                "description": desc,
                "morning_start_time": str(m_start) if m_start else None,
                "morning_end_time": str(m_end) if m_end else None,
                "evening_start_time": str(e_start) if e_start else None,
                "evening_end_time": str(e_end) if e_end else None,
                "emoji": emoji if emoji else "💊"
            })
        return result
    except psycopg2.DatabaseError as e:
        logging.error(f"❌ خطأ أثناء جلب الفئات: {e}")
        return []
    finally:
        close_db_connection(conn)
        logging.info("🔒 Database connection closed for get_categories")

if __name__ == "__main__":
    init_db_and_insert_data()
