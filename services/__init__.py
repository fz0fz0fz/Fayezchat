"""
This package contains service modules for the WhatsApp bot application.
"""
# دوال الجلسة
from .session import get_session, set_session, init_session_db
# خدمة المنبه
from .reminder import handle as handle_reminder, init_reminder_db
# خدمة بيانات الصيدليات والخدمات
from .db import get_categories, init_db_and_insert_data
# Connection Pooling (no longer needed, removed pool import)

__all__ = [
    "get_session",
    "set_session",
    "init_session_db",
    "handle_reminder",
    "init_reminder_db",
    "get_categories",
    "init_db_and_insert_data",
    # Removed "pool" from __all__ since it's no longer used
]
