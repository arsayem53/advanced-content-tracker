"""
Advanced Content Tracker
A Linux background daemon that tracks and classifies your digital activities.
"""

__version__ = "1.0.0"
__author__ = "Content Tracker Team"
__description__ = "Know exactly what you're watching, reading, and doing - every second."

from .core import (
    ContentTrackerDaemon,
    get_daemon,
    start_daemon,
    stop_daemon,
    capture_screenshot,
    get_active_window
)

from .storage import (
    Activity,
    ActivityType,
    ContentType,
    get_database
)

from .utils import (
    get_config,
    setup_logging,
    get_logger
)

__all__ = [
    # Core
    'ContentTrackerDaemon',
    'get_daemon',
    'start_daemon',
    'stop_daemon',
    'capture_screenshot',
    'get_active_window',
    
    # Storage
    'Activity',
    'ActivityType',
    'ContentType',
    'get_database',
    
    # Utils
    'get_config',
    'setup_logging',
    'get_logger',
    
    # Meta
    '__version__',
    '__author__',
    '__description__'
]
