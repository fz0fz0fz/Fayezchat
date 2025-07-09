import sqlite3
import os

DB_NAME = os.path.join(os.getcwd(), "services.db")

def init_db_and_insert_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

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

    c.execute("DELETE FROM categories")

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

    c.executemany('''
        INSERT OR IGNORE INTO categories
        (code, name, description, morning_start_time, morning_end_time, evening_start_time, evening_end_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', data)

    conn.commit()
    conn.close()
