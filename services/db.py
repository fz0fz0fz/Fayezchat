import psycopg2
import os
import logging

# تهيئة السجل (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# الحصول على DATABASE_URL من متغيرات البيئة
DB_URL = os.getenv("DATABASE_URL")

def init_db_and_insert_data():
    """
    تهيئة قاعدة البيانات وإدخال بيانات الصيدليات الافتراضية.
    يتم إنشاء جدول categories إن لم يكن موجودًا، وحذف البيانات القديمة، ثم إدخال بيانات جديدة.
    """
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set in environment variables.")
        return
    
    try:
        conn = psycopg2.connect(DB_URL)
        c = conn.cursor()

        # إنشاء جدول categories إن لم يكن موجودًا
        c.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                morning_start_time TEXT,
                morning_end_time TEXT,
                evening_start_time TEXT,
                evening_end_time TEXT,
                emoji TEXT DEFAULT '💊'
            )
        ''')

        # حذف جميع البيانات القديمة لضمان تحديث البيانات
        c.execute("DELETE FROM categories")

        # بيانات الصيدليات الافتراضية
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
            (
                "موعد", "موعد", "موعد زيارة أو مناسبة", None, None, None, None, "🩺"
            ),
            (
                "دواء", "دواء", "تذكير بتناول الدواء", None, None, None, None, "💊"
            ),
            (
                "تمرين", "تمرين", "تذكير بممارسة التمارين", None, None, None, None, "🏋️"
            ),
            (
                "اجتماع", "اجتماع", "تذكير باجتماع مهم", None, None, None, None, "🤝"
            ),
            (
                "فاتورة", "فاتورة", "تذكير بدفع فاتورة", None, None, None, None, "💳"
            )
        ]

        # إدخال البيانات مع تجاهل التكرارات
        c.executemany('''
            INSERT INTO categories (code, name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time, emoji)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (code) DO NOTHING
        ''', data)

        conn.commit()
        logging.info("✅ تم تهيئة جدول categories في قاعدة البيانات PostgreSQL وإدخال البيانات الافتراضية.")
    except Exception as e:
        logging.error(f"❌ خطأ أثناء تهيئة قاعدة البيانات PostgreSQL: {e}")
    finally:
        if conn is not None:
            conn.close()
            logging.info("🔒 Database connection closed for init_db_and_insert_data")

def get_categories():
    """
    جلب جميع الفئات (الصيدليات والتذكيرات) من قاعدة البيانات.
    يُرجع قائمة بالفئات يمكن استخدامها في التطبيق.
    """
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set in environment variables.")
        return []
    
    try:
        conn = psycopg2.connect(DB_URL)
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
                "morning_start_time": m_start,
                "morning_end_time": m_end,
                "evening_start_time": e_start,
                "evening_end_time": e_end,
                "emoji": emoji if emoji else "💊"
            })
        return result
    except Exception as e:
        logging.error(f"❌ خطأ أثناء جلب الفئات: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()
            logging.info("🔒 Database connection closed for get_categories")

# استدعاء التهيئة عند تحميل الملف
if __name__ == "__main__":
    init_db_and_insert_data()
