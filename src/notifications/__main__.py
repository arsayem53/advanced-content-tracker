"""
Module for testing notification functionality directly.
"""

if __name__ == "__main__":
    # Test notification
    sent = send_notification(
        title="Test Notification",
        message="This is a test notification from Content Tracker",
        timeout=3
    )
    print(f"Notification sent: {sent}")
