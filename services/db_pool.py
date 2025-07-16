import psycopg2
import os
import logging
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        logging.info("✅ Database connection initialized.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"❌ Failed to connect: {e}")
        return None

def close_db_connection(conn=None):
    if conn:
        try:
            conn.close()
            logging.info("🔒 Database connection closed.")
        except psycopg2.Error as e:
            logging.error(f"❌ Error closing connection: {e}")
