import psycopg2
import os
from urllib.parse import urlparse
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# متغير عالمي لتخزين الاتصال
connection = None

def get_db_connection():
    global connection
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logging.error("❌ DATABASE_URL not set in environment variables")
        return None
    
    try:
        result = urlparse(DATABASE_URL)
        db_config = {
            "dbname": result.path[1:],
            "user": result.username,
            "password": result.password,
            "host": result.hostname,
            "port": result.port
        }
        # إنشاء اتصال مباشر بدل الحوض
        connection = psycopg2.connect(**db_config)
        logging.info("✅ Database connection initialized successfully")
        return connection
    except psycopg2.Error as e:
        logging.error(f"❌ Failed to initialize database connection: {e}")
        return None

def close_db_connection():
    global connection
    if connection:
        try:
            connection.close()
            logging.info("🔒 Database connection closed")
        except psycopg2.Error as e:
            logging.error(f"❌ Error closing database connection: {e}")
        finally:
            connection = None

# تهيئة الاتصال عند تحميل الملف (اختياري، يمكن استدعاؤه يدويًا)
if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        close_db_connection()
