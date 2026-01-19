"""
Desktop Notifier - Sends desktop notifications for events.
"""

import time
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

try:
    # Try to import notify-py (modern notifications)
    import notify
    import notify
    HAS_NOTIFYPY = True
except ImportError:
    HAS_NOTIFYPY = False

try:
    # Try to import py-notifier (simpler API)
    from notifier import Notifier
    HAS_NOTIFIER = True
except ImportError:
    HAS_NOTIFIER = False

def send_notification(
    title: str,
    message: str,
    icon: Optional[str] = None,
    timeout: int = 5
) -> bool:
    """
    Send a system desktop notification.
    
    Args:
        title: Notification title
        message: Notification message
        icon: Optional icon path
        timeout: How long to show (seconds)
    
    Returns:
        True if notification sent
    """
    try:
        if HAS_NOTIFYPY:
            # Modern notification API
            if os.environ.get('DISPLAY'):
                notify.init()
                n = notify.Notification(title, message)
                if icon:
                    n.set_icon(icon)
                n.set_timeout(timeout * 1000)
                n.show()
                return True
        elif HAS_NOTIFIER:
            # Simple notifier
            notifier = Notifier()
            notifier.notify(title=title, message=message, app_name='ContentTracker', timeout=timeout)
            return True
        else:
            # Fallback to terminal print (for development)
            print(f"[NOTIFICATION] {title}: {message}")
            return True
            
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")
        return False

def should_notify(activity_info: Dict[str, Any]) -> bool:
    """
    Determine if a notification should be sent based on activity.
    
    Args:
        activity_info: Dict with activity details
        
    Returns:
        True if notification should be sent
    """
    # Check if we should notify based on rules
    if not activity_info.get('is_productive', False):
        # Only notify on non-productive activities after threshold
        duration = activity_info.get('duration', 0)
        if duration >= 1800:  # 30 minutes
            return True
        if activity_info.get('is_nsfw', False):
            return True
    
    return False


class NotificationType:
    """Types of notifications."""
    PRODUCTIVITY = "productivity"
    DISTRACTION = "distraction"
    NSFW = "nsfw"
    DAILY_SUMMARY = "daily_summary"

__all__ = [
    "NotificationType",
    "send_notification",
    "should_notify"
]
