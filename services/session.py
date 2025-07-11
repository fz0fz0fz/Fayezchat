# تخزين الجلسات مؤقتاً في الذاكرة
sessions = {}

def get_session(user_id):
    return sessions.get(user_id)

def save_session(user_id, value):
    sessions[user_id] = value

def clear_session(user_id):
    sessions.pop(user_id, None)
