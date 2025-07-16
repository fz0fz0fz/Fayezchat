import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        print("✅ Database connection initialized successfully")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def close_db_connection(conn=None):
    if conn is not None:
        try:
            conn.close()
            print("🔒 Database connection closed")
        except psycopg2.Error as e:
            print(f"❌ Error closing database connection: {e}")
