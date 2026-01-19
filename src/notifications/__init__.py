"""
Notifications module - Desktop notification handling.
"""

from .notifier import (
    NotificationType,
    send_notification,
    should_notify
)

__all__ = [
    "NotificationType",
    "send_notification",
    "should_notify"
]
