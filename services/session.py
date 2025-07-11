# services/session.py

# تخزين الجلسات مؤقتاً في الذاكرة
sessions = {}

def get_session(user_id):
    return sessions.get(user_id)

def set_session(user_id, state):
    if state:
        sessions[user_id] = state
    else:
        sessions.pop(user_id, None)
