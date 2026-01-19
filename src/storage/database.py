"""
Advanced Content Tracker - Database Operations
Handles all SQLite database operations with connection pooling and thread safety.
"""

import sqlite3
import threading
import os
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
import json

from .models import (
    Activity, 
    ContentSummary, 
    DailyStats, 
    AppUsage,
    WebsiteUsage, 
    FocusSession, 
    SCHEMA_SQL, 
    MIGRATIONS,
    ActivityType
)

logger = logging.getLogger(__name__)


class Database:
    """
    Thread-safe SQLite database handler with connection pooling.
    Manages all database operations for the content tracker.
    """
    
    def __init__(self, db_path: str = "data/activity.db", wal_mode: bool = True):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
            wal_mode: Enable WAL mode for better concurrency
        """
        self.db_path = db_path
        self.wal_mode = wal_mode
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Initialize database schema
        self._init_database()
        
        logger.info(f"Database initialized: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrency
            if self.wal_mode:
                self._local.connection.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys=ON")
            
            # Performance optimizations
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
        
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with automatic commit/rollback."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def _init_database(self):
        """Initialize database schema."""
        with self._lock:
            with self.get_cursor() as cursor:
                cursor.executescript(SCHEMA_SQL)
        logger.debug("Database schema initialized")
    
    # ==================== Activity Operations ====================
    
    def insert_activity(self, activity: Activity) -> int:
        """
        Insert a new activity record.
        
        Args:
            activity: Activity object to insert
            
        Returns:
            ID of inserted activity
        """
        data = activity.to_dict()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        
        with self.get_cursor() as cursor:
            cursor.execute(
                f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
                list(data.values())
            )
            activity_id = cursor.lastrowid
            logger.debug(f"Inserted activity {activity_id}: {activity.content_description[:50] if activity.content_description else 'N/A'}")
            return activity_id
    
    def get_activity(self, activity_id: int) -> Optional[Activity]:
        """
        Get a single activity by ID.
        
        Args:
            activity_id: Activity ID
            
        Returns:
            Activity object or None
        """
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
            row = cursor.fetchone()
            if row:
                return Activity.from_dict(dict(row))
        return None
    
    def get_activities(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        activity_type: Optional[str] = None,
        app_name: Optional[str] = None,
        website: Optional[str] = None,
        is_productive: Optional[bool] = None,
        is_nsfw: Optional[bool] = None,
        limit: int = 1000,
        offset: int = 0,
        order_desc: bool = True
    ) -> List[Activity]:
        """
        Query activities with filters.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            activity_type: Filter by activity type
            app_name: Filter by app name (partial match)
            website: Filter by website (partial match)
            is_productive: Filter by productivity
            is_nsfw: Filter by NSFW flag
            limit: Maximum results to return
            offset: Offset for pagination
            order_desc: Order by timestamp descending
            
        Returns:
            List of Activity objects
        """
        query = "SELECT * FROM activities WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat() if isinstance(start_time, datetime) else start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat() if isinstance(end_time, datetime) else end_time)
        
        if activity_type:
            query += " AND activity_type = ?"
            params.append(activity_type)
        
        if app_name:
            query += " AND app_name LIKE ?"
            params.append(f"%{app_name}%")
        
        if website:
            query += " AND website LIKE ?"
            params.append(f"%{website}%")
        
        if is_productive is not None:
            query += " AND is_productive = ?"
            params.append(1 if is_productive else 0)
        
        if is_nsfw is not None:
            query += " AND is_nsfw = ?"
            params.append(1 if is_nsfw else 0)
        
        order_dir = "DESC" if order_desc else "ASC"
        query += f" ORDER BY timestamp {order_dir} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return [Activity.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def get_recent_activities(self, hours: int = 24, limit: int = 1000) -> List[Activity]:
        """
        Get activities from the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum results
            
        Returns:
            List of Activity objects
        """
        start_time = datetime.now() - timedelta(hours=hours)
        return self.get_activities(start_time=start_time, limit=limit)
    
    def get_last_activity(self) -> Optional[Activity]:
        """
        Get the most recent activity.
        
        Returns:
            Most recent Activity or None
        """
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM activities ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return Activity.from_dict(dict(row))
        return None
    
    def get_activities_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """Get count of activities in time range."""
        query = "SELECT COUNT(*) FROM activities WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()[0]
    
    # ==================== Daily Stats Operations ====================
    
    def update_daily_stats(self, date: str = None):
        """
        Calculate and update daily statistics for a given date.
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            # Calculate stats from activities
            cursor.execute("""
                SELECT 
                    activity_type,
                    SUM(duration) as total_time,
                    COUNT(*) as session_count,
                    SUM(CASE WHEN is_nsfw = 1 THEN 1 ELSE 0 END) as nsfw_count
                FROM activities 
                WHERE date(timestamp) = ?
                GROUP BY activity_type
            """, (date,))
            
            stats = {}
            total_nsfw = 0
            for row in cursor.fetchall():
                stats[row['activity_type']] = {
                    'time': row['total_time'] or 0,
                    'count': row['session_count'] or 0
                }
                total_nsfw += row['nsfw_count'] or 0
            
            # Calculate totals
            total_time = sum(s['time'] for s in stats.values())
            total_sessions = sum(s['count'] for s in stats.values())
            
            # Get distinct app count (app switches approximation)
            cursor.execute("""
                SELECT COUNT(DISTINCT app_name) as app_count,
                       COUNT(DISTINCT website) as website_count
                FROM activities 
                WHERE date(timestamp) = ?
            """, (date,))
            counts = cursor.fetchone()
            app_switches = counts['app_count'] if counts else 0
            website_visits = counts['website_count'] if counts else 0
            
            # Get top app
            cursor.execute("""
                SELECT app_name, SUM(duration) as total
                FROM activities 
                WHERE date(timestamp) = ? AND app_name != '' AND app_name IS NOT NULL
                GROUP BY app_name 
                ORDER BY total DESC 
                LIMIT 1
            """, (date,))
            top_app_row = cursor.fetchone()
            top_app = top_app_row['app_name'] if top_app_row else ''
            
            # Get top website
            cursor.execute("""
                SELECT website, SUM(duration) as total
                FROM activities 
                WHERE date(timestamp) = ? AND website != '' AND website IS NOT NULL
                GROUP BY website 
                ORDER BY total DESC 
                LIMIT 1
            """, (date,))
            top_website_row = cursor.fetchone()
            top_website = top_website_row['website'] if top_website_row else ''
            
            # Get top content category
            cursor.execute("""
                SELECT content_category, SUM(duration) as total
                FROM activities 
                WHERE date(timestamp) = ? AND content_category != '' AND content_category IS NOT NULL
                GROUP BY content_category 
                ORDER BY total DESC 
                LIMIT 1
            """, (date,))
            top_cat_row = cursor.fetchone()
            top_category = top_cat_row['content_category'] if top_cat_row else ''
            
            # Calculate productivity score
            productive_time = stats.get('productive', {}).get('time', 0)
            educational_time = stats.get('educational', {}).get('time', 0)
            
            if total_time > 0:
                productivity_score = ((productive_time + educational_time * 0.8) / total_time) * 100
                productivity_score = min(100.0, max(0.0, productivity_score))
            else:
                productivity_score = 0.0
            
            # Insert or update daily stats
            cursor.execute("""
                INSERT OR REPLACE INTO daily_stats (
                    date, total_tracked_time, productive_time, educational_time,
                    entertainment_time, social_media_time, gaming_time, shopping_time,
                    news_time, adult_content_time, neutral_time, idle_time,
                    productivity_score, focus_score, total_sessions, app_switches,
                    website_visits, nsfw_detections, top_app, top_website, top_content_category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date,
                total_time,
                stats.get('productive', {}).get('time', 0),
                stats.get('educational', {}).get('time', 0),
                stats.get('entertainment', {}).get('time', 0),
                stats.get('social_media', {}).get('time', 0),
                stats.get('gaming', {}).get('time', 0),
                stats.get('shopping', {}).get('time', 0),
                stats.get('news', {}).get('time', 0),
                stats.get('adult', {}).get('time', 0),
                stats.get('neutral', {}).get('time', 0),
                stats.get('idle', {}).get('time', 0),
                productivity_score,
                0.0,  # focus_score - calculated separately
                total_sessions,
                app_switches,
                website_visits,
                total_nsfw,
                top_app,
                top_website,
                top_category
            ))
            
            logger.debug(f"Updated daily stats for {date}")
    
    def get_daily_stats(self, date: str = None) -> Optional[Dict[str, Any]]:
        """
        Get daily statistics for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dict with daily statistics or None
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def get_stats_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get daily statistics for a date range.
        
        Args:
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            
        Returns:
            List of daily stats dicts
        """
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM daily_stats WHERE date BETWEEN ? AND ? ORDER BY date",
                (start_date, end_date)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== App/Website Usage ====================
    
    def update_app_usage(self, date: str = None):
        """Update app usage summary for a date."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO app_usage (date, app_name, total_time, session_count, productivity_score)
                SELECT 
                    date(timestamp) as date,
                    app_name,
                    SUM(duration) as total_time,
                    COUNT(*) as session_count,
                    AVG(productivity_score) as productivity_score
                FROM activities 
                WHERE date(timestamp) = ? AND app_name != '' AND app_name IS NOT NULL
                GROUP BY date(timestamp), app_name
            """, (date,))
    
    def update_website_usage(self, date: str = None):
        """Update website usage summary for a date."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO website_usage (date, website, total_time, visit_count, productivity_score)
                SELECT 
                    date(timestamp) as date,
                    website,
                    SUM(duration) as total_time,
                    COUNT(*) as visit_count,
                    AVG(productivity_score) as productivity_score
                FROM activities 
                WHERE date(timestamp) = ? AND website != '' AND website IS NOT NULL
                GROUP BY date(timestamp), website
            """, (date,))
    
    def get_top_apps(self, date: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top apps by usage time.
        
        Args:
            date: Date in YYYY-MM-DD format
            limit: Maximum results
            
        Returns:
            List of app usage dicts
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT app_name, total_time, session_count, productivity_score
                FROM app_usage 
                WHERE date = ?
                ORDER BY total_time DESC 
                LIMIT ?
            """, (date, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_top_websites(self, date: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top websites by usage time.
        
        Args:
            date: Date in YYYY-MM-DD format
            limit: Maximum results
            
        Returns:
            List of website usage dicts
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT website, total_time, visit_count, productivity_score
                FROM website_usage 
                WHERE date = ?
                ORDER BY total_time DESC 
                LIMIT ?
            """, (date, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Search and Analysis ====================
    
    def search_activities(self, query: str, limit: int = 100) -> List[Activity]:
        """
        Search activities by content description, title, or extracted text.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching Activity objects
        """
        search_pattern = f"%{query}%"
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM activities 
                WHERE content_description LIKE ? 
                   OR content_title LIKE ? 
                   OR extracted_text LIKE ?
                   OR window_title LIKE ?
                   OR app_name LIKE ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, limit))
            return [Activity.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def get_time_by_category(self, date: str = None) -> Dict[str, int]:
        """
        Get time spent in each activity category for a date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dict mapping activity_type to total seconds
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT activity_type, SUM(duration) as total_time
                FROM activities 
                WHERE date(timestamp) = ?
                GROUP BY activity_type
            """, (date,))
            return {row['activity_type']: row['total_time'] or 0 for row in cursor.fetchall()}
    
    def get_hourly_breakdown(self, date: str = None) -> List[Dict[str, Any]]:
        """
        Get hourly activity breakdown for a date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of hourly breakdown dicts
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    strftime('%H', timestamp) as hour,
                    activity_type,
                    SUM(duration) as total_time,
                    COUNT(*) as session_count
                FROM activities 
                WHERE date(timestamp) = ?
                GROUP BY strftime('%H', timestamp), activity_type
                ORDER BY hour
            """, (date,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Focus Sessions ====================
    
    def insert_focus_session(self, session: FocusSession) -> int:
        """Insert a new focus session."""
        data = session.to_dict()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        
        with self.get_cursor() as cursor:
            cursor.execute(
                f"INSERT INTO focus_sessions ({columns}) VALUES ({placeholders})",
                list(data.values())
            )
            return cursor.lastrowid
    
    def update_focus_session(self, session_id: int, **kwargs):
        """Update a focus session."""
        if not kwargs:
            return
        
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [session_id]
        
        with self.get_cursor() as cursor:
            cursor.execute(
                f"UPDATE focus_sessions SET {set_clause} WHERE id = ?",
                values
            )
    
    def get_focus_sessions(self, date: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get focus sessions for a date."""
        query = "SELECT * FROM focus_sessions"
        params = []
        
        if date:
            query += " WHERE date(start_time) = ?"
            params.append(date)
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Settings ====================
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row['value'])
                except (json.JSONDecodeError, TypeError):
                    return row['value']
        return default
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        if not isinstance(value, str):
            value = json.dumps(value)
        
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat())
            )
    
    # ==================== Maintenance ====================
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """
        Delete data older than specified days.
        
        Args:
            days: Delete data older than this many days
            
        Returns:
            Number of deleted records
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM activities WHERE date(timestamp) < ?", (cutoff_date,))
            deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM daily_stats WHERE date < ?", (cutoff_date,))
            cursor.execute("DELETE FROM app_usage WHERE date < ?", (cutoff_date,))
            cursor.execute("DELETE FROM website_usage WHERE date < ?", (cutoff_date,))
            cursor.execute("DELETE FROM content_summary WHERE date < ?", (cutoff_date,))
            cursor.execute("DELETE FROM focus_sessions WHERE date(start_time) < ?", (cutoff_date,))
        
        logger.info(f"Cleaned up {deleted} old activity records (older than {days} days)")
        return deleted
    
    def vacuum(self):
        """Vacuum the database to reclaim space."""
        with self.get_cursor() as cursor:
            cursor.execute("VACUUM")
        logger.info("Database vacuumed")
    
    def backup(self, backup_path: str = None) -> str:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Destination path (auto-generated if None)
            
        Returns:
            Path to backup file
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        # Close connections before backup
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
        
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        return backup_path
    
    def get_database_size(self) -> int:
        """
        Get database file size in bytes.
        
        Returns:
            Size in bytes
        """
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path)
        return 0
    
    def get_record_count(self) -> Dict[str, int]:
        """
        Get count of records in each table.
        
        Returns:
            Dict mapping table name to record count
        """
        counts = {}
        tables = ['activities', 'daily_stats', 'app_usage', 'website_usage', 'content_summary', 'focus_sessions']
        
        with self.get_cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    counts[table] = 0
        
        return counts
    
    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
            except Exception as e:
                logger.warning(f"Error closing database: {e}")
            self._local.connection = None
        logger.debug("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# ============================================================
# Singleton Instance Management
# ============================================================

_db_instance: Optional[Database] = None
_db_lock = threading.Lock()


def get_database(db_path: str = "data/activity.db") -> Database:
    """
    Get or create the database singleton instance.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Database instance
    """
    global _db_instance
    
    with _db_lock:
        if _db_instance is None:
            _db_instance = Database(db_path)
    
    return _db_instance


def close_database():
    """Close the database singleton instance."""
    global _db_instance
    
    with _db_lock:
        if _db_instance:
            _db_instance.close()
            _db_instance = None
