# services/db.py
import sqlite3
import os

# مسار قاعدة البيانات
DB_NAME = os.path.join(os.getcwd(), "services.db")

def init_db_and_insert_data():
    """
    تهيئة قاعدة البيانات وإدخال بيانات الصيدليات الافتراضية.
    يتم إنشاء جدول categories إن لم يكن موجودًا، وحذف البيانات القديمة، ثم إدخال بيانات جديدة.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # إنشاء جدول categories إن لم يكن موجودًا
        c.execute('''
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

        # حذف جميع البيانات القديمة لضمان تحديث البيانات
        c.execute("DELETE FROM categories")

        # بيانات الصيدليات الافتراضية
        data = [
            (
                "صيدلية١",
                "صيدلية ركن أطلس (القرين)",
                "📞 0556945390\n📱 واتس اب\n📍 الموقع: https://maps.app.goo.gl/KGDcPGwvuym1E8YFA\n🚚 خدمة التوصيل: نعم",
                "08:00", "12:00", "16:00", "23:00"
            ),
            (
                "صيدلية٢",
                "صيدلية دواء القصيم",
                "📞 0500000000\n📍 الموقع: https://maps.app.goo.gl/test",
                "08:30", "12:30", "16:30", "23:30"
            )
        ]

        # إدخال البيانات مع تجاهل التكرارات
        c.executemany('''
            INSERT OR IGNORE INTO categories
            (code, name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)

        conn.commit()
        print("✅ تم تهيئة قاعدة البيانات services.db وإدخال البيانات الافتراضية.")
    except Exception as e:
        print(f"❌ خطأ أثناء تهيئة قاعدة البيانات services.db: {e}")
    finally:
        conn.close()

def get_categories():
    """
    جلب جميع الفئات (الصيدليات) من قاعدة البيانات.
    يُرجع قائمة بالفئات يمكن استخدامها في التطبيق.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT code, name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time FROM categories')
        categories = c.fetchall()
        return categories
    except Exception as e:
        print(f"❌ خطأ أثناء جلب الفئات: {e}")
        return []
    finally:
        conn.close()

# استدعاء التهيئة عند تحميل الملف
if __name__ == "__main__":
    init_db_and_insert_data()
