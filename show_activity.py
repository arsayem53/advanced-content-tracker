#!/usr/bin/env python3
"""
Simple script to run tracker with live activity display.
"""

import sys
import signal
from datetime import datetime

# Add src to path
sys.path.insert(0, '.')

from src.core.daemon import ContentTrackerDaemon
from src.utils.logger import setup_logging

def on_activity(activity):
    """Called when activity is detected."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Emoji based on activity type
    emoji_map = {
        'productive': '💻',
        'educational': '📖',
        'entertainment': '🎬',
        'social_media': '📱',
        'gaming': '🎮',
        'shopping': '🛒',
        'news': '📰',
        'adult': '🔞',
        'neutral': '⚪',
        'idle': '💤',
    }
    
    emoji = emoji_map.get(activity.activity_type, '❓')
    
    # Color based on productivity
    if activity.is_productive:
        color = '\033[92m'  # Green
    elif activity.activity_type in ['entertainment', 'social_media', 'gaming']:
        color = '\033[93m'  # Yellow
    elif activity.activity_type == 'adult':
        color = '\033[91m'  # Red
    else:
        color = '\033[0m'   # Default
    
    reset = '\033[0m'
    
    print(f"{timestamp} {emoji} {color}{activity.activity_type.upper():12}{reset} │ {activity.content_description[:50]}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║          Advanced Content Tracker - Live View             ║
╚═══════════════════════════════════════════════════════════╝
    """)
    print("Tracking started! Activity will appear below every 30 seconds.\n")
    print("TIME     TYPE          │ DESCRIPTION")
    print("─" * 70)
    
    # Setup logging (quiet mode)
    setup_logging(level='WARNING')
    
    # Create daemon
    daemon = ContentTrackerDaemon()
    
    # Set callback for live display
    daemon.set_activity_callback(on_activity)
    
    # Handle Ctrl+C
    def signal_handler(sig, frame):
        print("\n\n" + "─" * 70)
        print("Stopping tracker...")
        daemon.stop()
        print("✅ Tracker stopped. Run 'python main.py --report' to see summary.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start tracking
    daemon.start(blocking=True)


if __name__ == "__main__":
    main()
