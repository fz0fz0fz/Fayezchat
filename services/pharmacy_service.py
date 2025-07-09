import sqlite3
from datetime import datetime
import os

DB_NAME = os.path.join(os.getcwd(), "services.db")

def get_all_pharmacies():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, description FROM categories")
    result = c.fetchall()
    conn.close()
    return "\n\n".join([f"🏪 {row[0]}\n{row[1]}" for row in result])

def get_open_pharmacies():
    now = datetime.now().time()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT name, description, morning_start_time, morning_end_time,
               evening_start_time, evening_end_time
        FROM categories
    ''')
    result = c.fetchall()
    conn.close()

    open_now = []
    for row in result:
        name, description, m_start, m_end, e_start, e_end = row
        m_start = datetime.strptime(m_start, "%H:%M").time()
        m_end = datetime.strptime(m_end, "%H:%M").time()
        e_start = datetime.strptime(e_start, "%H:%M").time()
        e_end = datetime.strptime(e_end, "%H:%M").time()

        if (m_start <= now <= m_end) or (e_start <= now <= e_end):
            open_now.append(f"🏪 {name}\n{description}")

    return "\n\n".join(open_now) if open_now else "🚫 لا توجد صيدليات مفتوحة الآن."
