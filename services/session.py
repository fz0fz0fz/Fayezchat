import psycopg2
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
DB_URL = os.getenv("DATABASE_URL")

def init_session_db():
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set.")
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
        logging.info("✅ Sessions table initialized.")
    except Exception as e:
        logging.error(f"❌ Error initializing sessions: {e}")
    finally:
        if conn:
            conn.close()

def get_session(user_id: str) -> dict:
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set.")
        return {"state": "main_menu", "history": []}
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT state FROM sessions WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        if row and row[0]:
            state = json.loads(row[0])
            state.setdefault("history", [])
            return state
        return {"state": "main_menu", "history": []}
    except Exception as e:
        logging.error(f"❌ Error getting session for {user_id}: {e}")
        return {"state": "main_menu", "history": []}
    finally:
        if conn:
            conn.close()

def set_session(user_id: str, state: dict):
    if not DB_URL:
        logging.error("❌ DATABASE_URL not set.")
        return
    conn = None
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
    except Exception as e:
        logging.error(f"❌ Error setting session for {user_id}: {e}")
    finally:
        if conn:
            conn.close()
