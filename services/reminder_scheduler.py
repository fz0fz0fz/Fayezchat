# services/reminder_scheduler.py
import sqlite3
from datetime import datetime, timedelta
import requests
from typing import Dict, Optional

DB_PATH = "reminders.db"

# UltraMsg API configuration
# Replace these with your actual UltraMsg credentials
ULTRAMSG_API_URL = "https://api.ultramsg.com/instance<INSTANCE_ID>/messages/chat"
ULTRAMSG_TOKEN = "your_token_here"  # Replace with your actual Token
ULTRAMSG_INSTANCE_ID = "your_instance_id_here"  # Replace with your actual Instance ID

def send_whatsapp_message(user_id: str, message: str) -> bool:
    """
    Send a message to the user via WhatsApp using UltraMsg API.
    user_id: The WhatsApp number or ID of the user (format: 1234567890@c.us or as per UltraMsg)
    message: The text message to send
    Returns: True if sent successfully, False otherwise
    """
    try:
        # Prepare the API endpoint with your Instance ID
        api_url = ULTRAMSG_API_URL.replace("<INSTANCE_ID>", ULTRAMSG_INSTANCE_ID)
        
        # Prepare the payload for the POST request
        payload = {
            "token": ULTRAMSG_TOKEN,
            "to": user_id,  # Assuming user_id is the WhatsApp number in the correct format
            "body": message,
            "priority": 1  # Optional: Sets priority of the message
        }
        
        # Send the POST request to UltraMsg API
        response = requests.post(api_url, data=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            if "sent" in response_json and response_json["sent"] == "true":
                print(f"✅ WhatsApp message sent to {user_id}: {message}")
                return True
            else:
                print(f"❌ Failed to send WhatsApp message to {user_id}: {response_json}")
                return False
        else:
            print(f"❌ UltraMsg API error for {user_id}: Status code {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending WhatsApp message to {user_id}: {e}")
        return False

def check_reminders():
    """Check for reminders that are due and send notifications."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🔔 Checking reminders at {current_time}")
        
        cursor.execute('''
            SELECT id, user_id, reminder_type, message, remind_at, interval_days
            FROM reminders
            WHERE active = 1 AND remind_at <= ?
        ''', (current_time,))
        due_reminders = cursor.fetchall()

        if not due_reminders:
            print(f"✅ No due reminders found at {current_time}")
            conn.close()
            return

        for reminder in due_reminders:
            reminder_id, user_id, reminder_type, message, remind_at, interval_days = reminder
            notification_text = f"⏰ تذكير: {reminder_type} الآن!\n"
            if message:
                notification_text += f"التفاصيل: {message}\n"
            notification_text += f"🕒 الوقت: {remind_at}"
            
            # Send notification to user via WhatsApp
            if send_whatsapp_message(user_id, notification_text):
                print(f"✅ Notification sent to {user_id} for reminder {reminder_id}")
            else:
                print(f"❌ Failed to send notification to {user_id} for reminder {reminder_id}")

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

        print(f"✅ Processed {len(due_reminders)} due reminders at {current_time}")
    except Exception as e:
        print(f"❌ Error checking reminders: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    """Entry point for running the scheduler as a standalone script."""
    check_reminders()
