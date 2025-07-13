# services/reminder_scheduler.py
import sqlite3
from datetime import datetime
# Import your WhatsApp messaging function (placeholder)
# from services.whatsapp import send_whatsapp_message

DB_PATH = "reminders.db"

def check_reminders():
    """Check for reminders that are due and send notifications."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            SELECT id, user_id, reminder_type, message, remind_at, interval_days
            FROM reminders
            WHERE active = 1 AND remind_at <= ?
        ''', (current_time,))
        due_reminders = cursor.fetchall()

        for reminder in due_reminders:
            reminder_id, user_id, reminder_type, message, remind_at, interval_days = reminder
            notification_text = f"⏰ تذكير: {reminder_type} الآن!\n"
            if message:
                notification_text += f"التفاصيل: {message}\n"
            notification_text += f"🕒 الوقت: {remind_at}"
            
            # Send notification to user (replace with actual WhatsApp API call)
            print(f"📩 Sending reminder to {user_id}: {notification_text}")
            # send_whatsapp_message(user_id, notification_text)  # Placeholder

            # If recurring reminder, update remind_at based on interval_days
            if interval_days > 0:
                old_time = datetime.strptime(remind_at, "%Y-%m-%d %H:%M:%S")
                new_time = old_time + timedelta(days=interval_days)
                new_remind_at = new_time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('UPDATE reminders SET remind_at = ? WHERE id = ?', (new_remind_at, reminder_id))
                print(f"🔄 Updated recurring reminder {reminder_id} for {user_id} to {new_remind_at}")
            else:
                # Mark non-recurring reminder as inactive
                cursor.execute('UPDATE reminders SET active = 0 WHERE id = ?', (reminder_id,))
                print(f"✅ Marked non-recurring reminder {reminder_id} for {user_id} as inactive")
            
            # Update stats
            cursor.execute('''
                INSERT OR REPLACE INTO reminder_stats (user_id, reminders_sent)
                VALUES (?, COALESCE((SELECT reminders_sent FROM reminder_stats WHERE user_id = ?) + 1, 1))
            ''', (user_id, user_id))
            conn.commit()

        print(f"🔔 Checked reminders at {current_time}. Found
