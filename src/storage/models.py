"""
Advanced Content Tracker - Database Models
Defines the schema for all database tables using dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ActivityType(Enum):
    """High-level activity classification."""
    PRODUCTIVE = "productive"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    SOCIAL_MEDIA = "social_media"
    GAMING = "gaming"
    SHOPPING = "shopping"
    NEWS = "news"
    ADULT = "adult"
    NEUTRAL = "neutral"
    IDLE = "idle"
    UNKNOWN = "unknown"


class ContentType(Enum):
    """Type of content being consumed."""
    VIDEO = "video"
    ARTICLE = "article"
    CODE = "code"
    SOCIAL_FEED = "social_feed"
    DOCUMENT = "document"
    IMAGE = "image"
    GAME = "game"
    CHAT = "chat"
    EMAIL = "email"
    SEARCH = "search"
    FILE_MANAGER = "file_manager"
    TERMINAL = "terminal"
    BROWSER = "browser"
    UNKNOWN = "unknown"


class DetectionMethod(Enum):
    """Method used to detect/classify content."""
    CLIP = "clip"
    OCR = "ocr"
    URL = "url"
    RULES = "rules"
    IMAGE = "image"
    COMBINED = "combined"
    MANUAL = "manual"


@dataclass
class Activity:
    """
    Main activity record - represents a single tracking snapshot.
    This is the primary data model for storing user activity.
    """
    # Primary key (set by database)
    id: Optional[int] = None
    
    # Timestamp of the activity
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Application/Window information
    app_name: str = ""
    window_title: str = ""
    process_name: str = ""
    process_id: Optional[int] = None
    
    # Website information (for browsers)
    website: str = ""
    url: str = ""
    
    # Content classification
    content_type: str = ContentType.UNKNOWN.value
    content_category: str = ""  # e.g., "cartoon", "music_video", "tutorial"
    content_description: str = ""  # e.g., "Watching: Minecraft gameplay"
    content_title: str = ""  # Extracted title if available
    
    # Activity classification
    activity_type: str = ActivityType.UNKNOWN.value
    is_productive: bool = False
    productivity_score: float = 0.0  # -1.0 to 1.0
    
    # Detection details
    detection_method: str = DetectionMethod.RULES.value
    confidence: float = 0.0  # 0.0 to 1.0
    
    # NSFW detection
    nsfw_score: float = 0.0  # 0.0 to 1.0
    is_nsfw: bool = False
    
    # Timing
    duration: int = 30  # seconds (default to screenshot interval)
    
    # Screenshot path (optional, if screenshots are saved)
    screenshot_path: str = ""
    
    # Metadata flags
    is_idle: bool = False
    is_excluded: bool = False  # Excluded by privacy settings
    
    # OCR extracted text (for debugging/analysis, truncated)
    extracted_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'app_name': self.app_name or "",
            'window_title': self.window_title or "",
            'process_name': self.process_name or "",
            'process_id': self.process_id,
            'website': self.website or "",
            'url': self.url or "",
            'content_type': self.content_type or "unknown",
            'content_category': self.content_category or "",
            'content_description': self.content_description or "",
            'content_title': self.content_title or "",
            'activity_type': self.activity_type or "unknown",
            'is_productive': self.is_productive,
            'productivity_score': self.productivity_score,
            'detection_method': self.detection_method or "rules",
            'confidence': self.confidence,
            'nsfw_score': self.nsfw_score,
            'is_nsfw': self.is_nsfw,
            'duration': self.duration,
            'screenshot_path': self.screenshot_path or "",
            'is_idle': self.is_idle,
            'is_excluded': self.is_excluded,
            'extracted_text': (self.extracted_text or "")[:1000]  # Limit text length
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Activity':
        """Create Activity from dictionary (database row)."""
        # Handle timestamp conversion
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except (ValueError, TypeError):
                data['timestamp'] = datetime.now()
        
        # Filter to only valid fields
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)
    
    @classmethod
    def from_row(cls, row) -> 'Activity':
        """Create Activity from SQLite Row object."""
        if row is None:
            return None
        return cls.from_dict(dict(row))
    
    def __str__(self) -> str:
        return f"Activity({self.app_name}: {self.content_description[:50]})"
    
    def __repr__(self) -> str:
        return f"Activity(id={self.id}, app={self.app_name}, type={self.activity_type})"


@dataclass
class ContentSummary:
    """
    Aggregated content type summary for a specific date.
    Used for quick lookups of daily content breakdowns.
    """
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD format
    content_type: str = ""
    content_category: str = ""
    total_time: int = 0  # seconds
    session_count: int = 0
    avg_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'content_type': self.content_type,
            'content_category': self.content_category,
            'total_time': self.total_time,
            'session_count': self.session_count,
            'avg_confidence': self.avg_confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentSummary':
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)


@dataclass
class DailyStats:
    """
    Daily statistics summary.
    Aggregated view of a full day's activity.
    """
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD format
    
    # Time breakdown (all in seconds)
    total_tracked_time: int = 0
    productive_time: int = 0
    educational_time: int = 0
    entertainment_time: int = 0
    social_media_time: int = 0
    gaming_time: int = 0
    shopping_time: int = 0
    news_time: int = 0
    adult_content_time: int = 0
    neutral_time: int = 0
    idle_time: int = 0
    
    # Calculated scores
    productivity_score: float = 0.0  # 0-100
    focus_score: float = 0.0  # 0-100
    
    # Counts
    total_sessions: int = 0
    app_switches: int = 0
    website_visits: int = 0
    nsfw_detections: int = 0
    
    # Top items
    top_app: str = ""
    top_website: str = ""
    top_content_category: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'total_tracked_time': self.total_tracked_time,
            'productive_time': self.productive_time,
            'educational_time': self.educational_time,
            'entertainment_time': self.entertainment_time,
            'social_media_time': self.social_media_time,
            'gaming_time': self.gaming_time,
            'shopping_time': self.shopping_time,
            'news_time': self.news_time,
            'adult_content_time': self.adult_content_time,
            'neutral_time': self.neutral_time,
            'idle_time': self.idle_time,
            'productivity_score': self.productivity_score,
            'focus_score': self.focus_score,
            'total_sessions': self.total_sessions,
            'app_switches': self.app_switches,
            'website_visits': self.website_visits,
            'nsfw_detections': self.nsfw_detections,
            'top_app': self.top_app,
            'top_website': self.top_website,
            'top_content_category': self.top_content_category
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyStats':
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)
    
    @property
    def productive_percentage(self) -> float:
        """Calculate productive time as percentage of total."""
        if self.total_tracked_time == 0:
            return 0.0
        return (self.productive_time / self.total_tracked_time) * 100
    
    @property
    def distraction_percentage(self) -> float:
        """Calculate distraction time as percentage of total."""
        if self.total_tracked_time == 0:
            return 0.0
        distraction = self.entertainment_time + self.social_media_time + self.gaming_time
        return (distraction / self.total_tracked_time) * 100


@dataclass
class AppUsage:
    """
    Application usage tracking summary.
    Aggregated per-app statistics for a date.
    """
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD format
    app_name: str = ""
    total_time: int = 0  # seconds
    session_count: int = 0
    productivity_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'app_name': self.app_name,
            'total_time': self.total_time,
            'session_count': self.session_count,
            'productivity_score': self.productivity_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppUsage':
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)


@dataclass
class WebsiteUsage:
    """
    Website usage tracking summary.
    Aggregated per-website statistics for a date.
    """
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD format
    website: str = ""
    total_time: int = 0  # seconds
    visit_count: int = 0
    content_categories: str = ""  # JSON list of categories
    productivity_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'website': self.website,
            'total_time': self.total_time,
            'visit_count': self.visit_count,
            'content_categories': self.content_categories,
            'productivity_score': self.productivity_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebsiteUsage':
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)


@dataclass
class FocusSession:
    """
    Focus mode session tracking.
    Records details of focus/pomodoro sessions.
    """
    id: Optional[int] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    planned_duration: int = 25  # minutes
    actual_duration: int = 0  # minutes
    completed: bool = False
    distractions: int = 0  # Number of distraction attempts
    blocked_attempts: int = 0  # Number of blocked site/app attempts
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_time': self.start_time.isoformat() if isinstance(self.start_time, datetime) else self.start_time,
            'end_time': self.end_time.isoformat() if isinstance(self.end_time, datetime) and self.end_time else None,
            'planned_duration': self.planned_duration,
            'actual_duration': self.actual_duration,
            'completed': self.completed,
            'distractions': self.distractions,
            'blocked_attempts': self.blocked_attempts,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FocusSession':
        # Handle datetime conversion
        for field_name in ['start_time', 'end_time']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except (ValueError, TypeError):
                    if field_name == 'start_time':
                        data[field_name] = datetime.now()
                    else:
                        data[field_name] = None
        
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)


# ============================================================
# SQL Schema Definitions
# ============================================================

SCHEMA_SQL = """
-- ============================================================
-- Advanced Content Tracker - Database Schema
-- ============================================================

-- Main activity log table
-- Stores every captured activity snapshot
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    
    -- App/Window info
    app_name TEXT DEFAULT '',
    window_title TEXT DEFAULT '',
    process_name TEXT DEFAULT '',
    process_id INTEGER,
    
    -- Website info (for browsers)
    website TEXT DEFAULT '',
    url TEXT DEFAULT '',
    
    -- Content classification
    content_type TEXT DEFAULT 'unknown',
    content_category TEXT DEFAULT '',
    content_description TEXT DEFAULT '',
    content_title TEXT DEFAULT '',
    
    -- Activity classification
    activity_type TEXT DEFAULT 'unknown',
    is_productive BOOLEAN DEFAULT 0,
    productivity_score REAL DEFAULT 0.0,
    
    -- Detection details
    detection_method TEXT DEFAULT 'rules',
    confidence REAL DEFAULT 0.0,
    
    -- NSFW detection
    nsfw_score REAL DEFAULT 0.0,
    is_nsfw BOOLEAN DEFAULT 0,
    
    -- Timing
    duration INTEGER DEFAULT 30,
    
    -- Screenshot path (if saved)
    screenshot_path TEXT DEFAULT '',
    
    -- Metadata
    is_idle BOOLEAN DEFAULT 0,
    is_excluded BOOLEAN DEFAULT 0,
    extracted_text TEXT DEFAULT ''
);

-- Indexes for common queries on activities table
CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp);
CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date(timestamp));
CREATE INDEX IF NOT EXISTS idx_activities_app ON activities(app_name);
CREATE INDEX IF NOT EXISTS idx_activities_website ON activities(website);
CREATE INDEX IF NOT EXISTS idx_activities_activity_type ON activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_content_type ON activities(content_type);
CREATE INDEX IF NOT EXISTS idx_activities_is_productive ON activities(is_productive);
CREATE INDEX IF NOT EXISTS idx_activities_is_nsfw ON activities(is_nsfw);

-- Content type summary table (aggregated)
CREATE TABLE IF NOT EXISTS content_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    content_type TEXT NOT NULL,
    content_category TEXT DEFAULT '',
    total_time INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    avg_confidence REAL DEFAULT 0.0,
    UNIQUE(date, content_type, content_category)
);

CREATE INDEX IF NOT EXISTS idx_content_summary_date ON content_summary(date);

-- Daily statistics table
CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    
    -- Time breakdown (seconds)
    total_tracked_time INTEGER DEFAULT 0,
    productive_time INTEGER DEFAULT 0,
    educational_time INTEGER DEFAULT 0,
    entertainment_time INTEGER DEFAULT 0,
    social_media_time INTEGER DEFAULT 0,
    gaming_time INTEGER DEFAULT 0,
    shopping_time INTEGER DEFAULT 0,
    news_time INTEGER DEFAULT 0,
    adult_content_time INTEGER DEFAULT 0,
    neutral_time INTEGER DEFAULT 0,
    idle_time INTEGER DEFAULT 0,
    
    -- Scores
    productivity_score REAL DEFAULT 0.0,
    focus_score REAL DEFAULT 0.0,
    
    -- Counts
    total_sessions INTEGER DEFAULT 0,
    app_switches INTEGER DEFAULT 0,
    website_visits INTEGER DEFAULT 0,
    nsfw_detections INTEGER DEFAULT 0,
    
    -- Top items
    top_app TEXT DEFAULT '',
    top_website TEXT DEFAULT '',
    top_content_category TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);

-- App usage summary table
CREATE TABLE IF NOT EXISTS app_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    app_name TEXT NOT NULL,
    total_time INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    productivity_score REAL DEFAULT 0.0,
    UNIQUE(date, app_name)
);

CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(date);
CREATE INDEX IF NOT EXISTS idx_app_usage_app ON app_usage(app_name);

-- Website usage summary table
CREATE TABLE IF NOT EXISTS website_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    website TEXT NOT NULL,
    total_time INTEGER DEFAULT 0,
    visit_count INTEGER DEFAULT 0,
    content_categories TEXT DEFAULT '[]',
    productivity_score REAL DEFAULT 0.0,
    UNIQUE(date, website)
);

CREATE INDEX IF NOT EXISTS idx_website_usage_date ON website_usage(date);
CREATE INDEX IF NOT EXISTS idx_website_usage_website ON website_usage(website);

-- Focus sessions table
CREATE TABLE IF NOT EXISTS focus_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    planned_duration INTEGER DEFAULT 25,
    actual_duration INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT 0,
    distractions INTEGER DEFAULT 0,
    blocked_attempts INTEGER DEFAULT 0,
    notes TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_focus_sessions_start ON focus_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_focus_sessions_date ON focus_sessions(date(start_time));

-- Settings/preferences table (key-value store)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Schema version tracking
INSERT OR IGNORE INTO settings (key, value) VALUES ('schema_version', '1');
"""

# Migration queries for future schema updates
MIGRATIONS = {
    1: """
        -- Version 1: Initial schema
        -- Already defined in SCHEMA_SQL above
    """,
    2: """
        -- Version 2: Add content_title column if not exists
        ALTER TABLE activities ADD COLUMN content_title TEXT DEFAULT '';
    """,
    3: """
        -- Version 3: Add focus mode tables
        -- focus_sessions table already in initial schema
    """,
}
