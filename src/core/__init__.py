"""
Core module - Main daemon, window monitoring, and screenshot capture.
"""

from .screenshot import (
    ScreenshotCapture,
    get_screenshot_capture,
    capture_screenshot
)

from .monitor import (
    WindowMonitor,
    WindowInfo,
    get_window_monitor,
    get_active_window
)

from .daemon import (
    ContentTrackerDaemon,
    DaemonState,
    get_daemon,
    start_daemon,
    stop_daemon
)

__all__ = [
    # Screenshot
    'ScreenshotCapture',
    'get_screenshot_capture',
    'capture_screenshot',
    
    # Monitor
    'WindowMonitor',
    'WindowInfo',
    'get_window_monitor',
    'get_active_window',
    
    # Daemon
    'ContentTrackerDaemon',
    'DaemonState',
    'get_daemon',
    'start_daemon',
    'stop_daemon'
]
