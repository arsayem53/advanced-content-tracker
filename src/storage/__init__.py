"""
Storage module - Database operations and data models.
Handles all persistent data storage for the content tracker.
"""

from .models import (
    Activity,
    ActivityType,
    ContentType,
    DetectionMethod,
    ContentSummary,
    DailyStats,
    AppUsage,
    WebsiteUsage,
    FocusSession,
    SCHEMA_SQL,
    MIGRATIONS
)

from .database import (
    Database,
    get_database,
    close_database
)

__all__ = [
    # Models
    'Activity',
    'ActivityType',
    'ContentType',
    'DetectionMethod',
    'ContentSummary',
    'DailyStats',
    'AppUsage',
    'WebsiteUsage',
    'FocusSession',
    'SCHEMA_SQL',
    'MIGRATIONS',
    
    # Database
    'Database',
    'get_database',
    'close_database'
]
