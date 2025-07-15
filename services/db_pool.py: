import psycopg2
import os
from urllib.parse import urlparse
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

pool = None
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        result = urlparse(DATABASE_URL)
        db_config = {
            "dbname": result.path[1:],
            "user": result.username,
            "password": result.password,
            "host": result.hostname,
            "port": result.port
        }
        pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **db_config
        )
        logging.info("✅ Database connection pool initialized successfully")
    except Exception as e:
        logging.error(f"❌ Failed to initialize database connection pool: {e}")
else:
    logging.error("❌ DATABASE_URL not set in environment variables")
