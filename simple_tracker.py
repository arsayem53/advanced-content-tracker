#!/usr/bin/env python3
"""
Simple Content Tracker - Reliable version with live output.
"""

import sys
import time
import signal
from datetime import datetime

sys.path.insert(0, '.')

# Setup minimal logging
import logging
logging.basicConfig(level=logging.WARNING, format='%(message)s')

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

print("""
╔═══════════════════════════════════════════════════════════════════════╗
║              Simple Content Tracker - Live View                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")

# Initialize components
print("⏳ Loading components...")

from src.core.screenshot import get_screenshot_capture
from src.core.monitor import get_window_monitor
from src.storage.database import get_database
from src.storage.models import Activity
from src.analyzers.content_classifier import ContentClassifier

capture = get_screenshot_capture()
monitor = get_window_monitor()
db = get_database()
classifier = ContentClassifier()

print("✅ All components loaded!")
print("")
print("Capturing every 30 seconds. Press Ctrl+C to stop.\n")
print("TIME     │ TYPE         │ APP                │ DESCRIPTION")
print("─" * 75)

# Track running state
running = True

def signal_handler(sig, frame):
    global running
    running = False
    print("\n\n🛑 Stopping...")

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Activity counter
activity_count = 0

# Main loop
while running:
    try:
        loop_start = time.time()
        
        # 1. Capture screenshot
        screenshot = capture.capture()
        if screenshot is None:
            print(f"{datetime.now().strftime('%H:%M:%S')} │ ⚠️ Screenshot failed")
            time.sleep(30)
            continue
        
        # 2. Get active window
        window = monitor.get_active_window()
        
        # 3. Classify content
        result = classifier.classify(screenshot, window)
        
        # 4. Create activity record
        activity = Activity(
            timestamp=datetime.now(),
            app_name=window.app_name if window else "Unknown",
            window_title=window.window_title if window else "",
            process_name=window.process_name if window else "",
            website=window.url if window and window.is_browser else "",
            url=window.url if window and window.is_browser else "",
            content_type=result.get('content_type', 'unknown'),
            content_category=result.get('content_category', ''),
            content_description=result.get('content_description', ''),
            activity_type=result.get('activity_type', 'neutral'),
            is_productive=result.get('is_productive', False),
            productivity_score=result.get('productivity_score', 0.0),
            detection_method=result.get('detection_method', 'rules'),
            confidence=result.get('confidence', 0.0),
            nsfw_score=result.get('nsfw_score', 0.0),
            is_nsfw=result.get('is_nsfw', False),
            duration=30,
        )
        
        # 5. Save to database
        db.insert_activity(activity)
        activity_count += 1
        
        # 6. Display output
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
        
        # Color output
        if activity.is_productive:
            color = '\033[92m'  # Green
        elif activity.activity_type in ['entertainment', 'social_media', 'gaming']:
            color = '\033[93m'  # Yellow  
        elif activity.activity_type == 'adult':
            color = '\033[91m'  # Red
        else:
            color = '\033[0m'
        reset = '\033[0m'
        
        app_name = (activity.app_name or "Unknown")[:18]
        description = (activity.content_description or activity.activity_type)[:30]
        
        print(f"{datetime.now().strftime('%H:%M:%S')} │ {emoji} {color}{activity.activity_type:12}{reset} │ {app_name:18} │ {description}")
        
        # 7. Calculate how long to wait
        elapsed = time.time() - loop_start
        wait_time = max(0, 30 - elapsed)
        
        # Wait for next capture
        if running and wait_time > 0:
            time.sleep(wait_time)
        
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"{datetime.now().strftime('%H:%M:%S')} │ ❌ Error: {e}")
        time.sleep(30)

# Cleanup
print("─" * 75)
print(f"\n✅ Tracked {activity_count} activities.")
print("📊 Run 'python main.py --report' to see full report.\n")
