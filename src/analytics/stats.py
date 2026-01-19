"""
Statistics Calculator - Computes aggregates and metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


def format_duration(seconds: int) -> str:
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"


class StatsCalculator:
    """
    Calculates various statistics from activity data.
    """
    
    # Productivity weights
    PRODUCTIVITY_WEIGHTS = {
        'productive': 1.0,
        'educational': 0.8,
        'neutral': 0.0,
        'news': -0.1,
        'shopping': -0.2,
        'entertainment': -0.3,
        'social_media': -0.4,
        'gaming': -0.3,
        'adult': -1.0,
        'idle': 0.0,
        'unknown': 0.0,
    }
    
    def __init__(self, database=None):
        """Initialize StatsCalculator."""
        self.db = database
        self.logger = logging.getLogger("StatsCalculator")
    
    def get_daily_summary(self, date_str: str = None) -> Dict[str, Any]:
        """
        Get comprehensive daily summary.
        
        Args:
            date_str: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dict with daily statistics
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        if self.db is None:
            from src.storage.database import get_database
            self.db = get_database()
        
        # Try to get cached stats first
        cached = self.db.get_daily_stats(date_str)
        if cached:
            return cached
        
        # Calculate from activities
        try:
            start = datetime.strptime(date_str, "%Y-%m-%d")
            end = start + timedelta(days=1)
            
            activities = self.db.get_activities(
                start_time=start,
                end_time=end,
                limit=10000
            )
            
            if not activities:
                return self._empty_summary(date_str)
            
            # Calculate aggregates
            time_by_type = defaultdict(int)
            total_duration = 0
            total_confidence = 0
            nsfw_count = 0
            
            for activity in activities:
                duration = getattr(activity, 'duration', 30)
                time_by_type[activity.activity_type] += duration
                total_duration += duration
                total_confidence += activity.confidence
                if activity.is_nsfw:
                    nsfw_count += 1
            
            # Calculate productivity score
            productivity_score = self._calculate_productivity_score(time_by_type, total_duration)
            
            summary = {
                'date': date_str,
                'total_tracked_time': total_duration,
                'productive_time': time_by_type.get('productive', 0),
                'educational_time': time_by_type.get('educational', 0),
                'entertainment_time': time_by_type.get('entertainment', 0),
                'social_media_time': time_by_type.get('social_media', 0),
                'gaming_time': time_by_type.get('gaming', 0),
                'shopping_time': time_by_type.get('shopping', 0),
                'news_time': time_by_type.get('news', 0),
                'adult_content_time': time_by_type.get('adult', 0),
                'neutral_time': time_by_type.get('neutral', 0),
                'idle_time': time_by_type.get('idle', 0),
                'productivity_score': productivity_score,
                'total_sessions': len(activities),
                'nsfw_detections': nsfw_count,
                'avg_confidence': total_confidence / len(activities) if activities else 0,
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get daily summary: {e}")
            return self._empty_summary(date_str)
    
    def _empty_summary(self, date_str: str) -> Dict[str, Any]:
        """Return empty summary structure."""
        return {
            'date': date_str,
            'total_tracked_time': 0,
            'productive_time': 0,
            'educational_time': 0,
            'entertainment_time': 0,
            'social_media_time': 0,
            'gaming_time': 0,
            'shopping_time': 0,
            'news_time': 0,
            'adult_content_time': 0,
            'neutral_time': 0,
            'idle_time': 0,
            'productivity_score': 0,
            'total_sessions': 0,
            'nsfw_detections': 0,
            'avg_confidence': 0,
        }
    
    def _calculate_productivity_score(self, time_by_type: Dict[str, int], total_time: int) -> float:
        """Calculate productivity score (0-100)."""
        if total_time == 0:
            return 0.0
        
        weighted_sum = 0
        for activity_type, duration in time_by_type.items():
            weight = self.PRODUCTIVITY_WEIGHTS.get(activity_type, 0)
            weighted_sum += weight * duration
        
        # Normalize to 0-100 scale
        # Max positive score: 100 (all productive)
        # Min score: 0 (all negative activities)
        score = ((weighted_sum / total_time) + 1) * 50
        return max(0, min(100, score))
    
    def get_weekly_breakdown(self, days: int = 7) -> Dict[str, Any]:
        """
        Get weekly breakdown of activity types.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with time per activity type
        """
        if self.db is None:
            from src.storage.database import get_database
            self.db = get_database()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            activities = self.db.get_activities(
                start_time=start_date,
                end_time=end_date,
                limit=50000
            )
            
            weekly_time = defaultdict(int)
            daily_breakdown = defaultdict(lambda: defaultdict(int))
            
            for activity in activities:
                duration = getattr(activity, 'duration', 30)
                weekly_time[activity.activity_type] += duration
                
                day = activity.timestamp.strftime('%Y-%m-%d') if hasattr(activity.timestamp, 'strftime') else str(activity.timestamp)[:10]
                daily_breakdown[day][activity.activity_type] += duration
            
            return {
                'period_days': days,
                'total_by_type': dict(weekly_time),
                'daily_breakdown': {k: dict(v) for k, v in daily_breakdown.items()},
                'total_time': sum(weekly_time.values()),
            }
            
        except Exception as e:
            self.logger.error(f"Weekly breakdown failed: {e}")
            return {'period_days': days, 'total_by_type': {}, 'daily_breakdown': {}, 'total_time': 0}
    
    def get_time_by_category(self, date_str: str = None) -> Dict[str, int]:
        """
        Get time spent by activity type.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            
        Returns:
            Dict mapping activity_type to seconds
        """
        summary = self.get_daily_summary(date_str)
        
        return {
            'productive': summary.get('productive_time', 0),
            'educational': summary.get('educational_time', 0),
            'entertainment': summary.get('entertainment_time', 0),
            'social_media': summary.get('social_media_time', 0),
            'gaming': summary.get('gaming_time', 0),
            'shopping': summary.get('shopping_time', 0),
            'news': summary.get('news_time', 0),
            'adult': summary.get('adult_content_time', 0),
            'neutral': summary.get('neutral_time', 0),
            'idle': summary.get('idle_time', 0),
        }
    
    def get_top_activities(self, date_str: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top activities by time.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            limit: Maximum items to return
            
        Returns:
            List of activity dicts
        """
        if self.db is None:
            from src.storage.database import get_database
            self.db = get_database()
        
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            start = datetime.strptime(date_str, "%Y-%m-%d")
            end = start + timedelta(days=1)
            
            activities = self.db.get_activities(start_time=start, end_time=end, limit=10000)
            
            # Aggregate by content description
            activity_times = defaultdict(lambda: {'time': 0, 'count': 0, 'type': ''})
            
            for a in activities:
                key = a.content_description or a.app_name or 'Unknown'
                activity_times[key]['time'] += getattr(a, 'duration', 30)
                activity_times[key]['count'] += 1
                activity_times[key]['type'] = a.activity_type
            
            # Sort by time
            sorted_activities = sorted(
                activity_times.items(),
                key=lambda x: x[1]['time'],
                reverse=True
            )[:limit]
            
            return [
                {
                    'description': desc,
                    'total_time': data['time'],
                    'session_count': data['count'],
                    'activity_type': data['type'],
                }
                for desc, data in sorted_activities
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get top activities: {e}")
            return []
