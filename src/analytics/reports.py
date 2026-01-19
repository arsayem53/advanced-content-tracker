"""
Report Generator - Creates various report formats.
"""

import os
import json
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

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


class ReportGenerator:
    """
    Generates reports in various formats (text, JSON, CSV).
    """
    
    def __init__(self, database=None):
        """Initialize ReportGenerator."""
        self.db = database
        self.logger = logging.getLogger("ReportGenerator")
    
    def generate_daily_report(self, date_str: str = None) -> Dict[str, Any]:
        """
        Generate a complete daily report.
        
        Args:
            date_str: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dict containing all report data
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        if self.db is None:
            from src.storage.database import get_database
            self.db = get_database()
        
        try:
            start = datetime.strptime(date_str, "%Y-%m-%d")
            end = start + timedelta(days=1)
            
            activities = self.db.get_activities(start_time=start, end_time=end, limit=10000)
            
            # Build report
            report = {
                'date': date_str,
                'generated_at': datetime.now().isoformat(),
                'summary': self._build_summary(activities),
                'by_activity_type': self._group_by_type(activities),
                'top_apps': self.db.get_top_apps(date_str, limit=10),
                'top_websites': self.db.get_top_websites(date_str, limit=10),
                'hourly_breakdown': self._hourly_breakdown(activities),
                'recent_activities': [
                    {
                        'time': a.timestamp.isoformat() if hasattr(a.timestamp, 'isoformat') else str(a.timestamp),
                        'app': a.app_name,
                        'type': a.activity_type,
                        'description': a.content_description,
                    }
                    for a in activities[-20:]
                ],
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Daily report generation failed: {e}")
            return {'date': date_str, 'error': str(e)}
    
    def _build_summary(self, activities: List) -> Dict[str, Any]:
        """Build summary statistics."""
        if not activities:
            return {
                'total_time': 0,
                'total_sessions': 0,
                'productivity_score': 0,
            }
        
        total_time = sum(getattr(a, 'duration', 30) for a in activities)
        productive_time = sum(
            getattr(a, 'duration', 30) for a in activities 
            if a.activity_type in ['productive', 'educational']
        )
        
        productivity_score = (productive_time / total_time * 100) if total_time > 0 else 0
        
        return {
            'total_time': total_time,
            'total_time_formatted': format_duration(total_time),
            'total_sessions': len(activities),
            'productive_time': productive_time,
            'productive_time_formatted': format_duration(productive_time),
            'productivity_score': round(productivity_score, 1),
        }
    
    def _group_by_type(self, activities: List) -> Dict[str, Dict]:
        """Group activities by type."""
        from collections import defaultdict
        
        by_type = defaultdict(lambda: {'time': 0, 'count': 0})
        
        for a in activities:
            duration = getattr(a, 'duration', 30)
            by_type[a.activity_type]['time'] += duration
            by_type[a.activity_type]['count'] += 1
        
        # Add formatted times
        result = {}
        for activity_type, data in by_type.items():
            result[activity_type] = {
                'time': data['time'],
                'time_formatted': format_duration(data['time']),
                'count': data['count'],
            }
        
        return result
    
    def _hourly_breakdown(self, activities: List) -> Dict[int, Dict]:
        """Break down activities by hour."""
        from collections import defaultdict
        
        by_hour = defaultdict(lambda: {'time': 0, 'count': 0})
        
        for a in activities:
            if hasattr(a.timestamp, 'hour'):
                hour = a.timestamp.hour
            else:
                try:
                    hour = datetime.fromisoformat(str(a.timestamp)).hour
                except:
                    continue
            
            duration = getattr(a, 'duration', 30)
            by_hour[hour]['time'] += duration
            by_hour[hour]['count'] += 1
        
        return dict(by_hour)
    
    def print_text_report(self, report: Dict[str, Any]):
        """Print report as formatted text to console."""
        print(f"\n📊 Activity Report for {report.get('date', 'Unknown')}")
        print("=" * 50)
        
        summary = report.get('summary', {})
        
        if summary.get('total_time', 0) == 0:
            print("  No data available for this date.")
            return
        
        print(f"\n⏱️  Total Tracked Time: {summary.get('total_time_formatted', '0s')}")
        print(f"📈 Productivity Score: {summary.get('productivity_score', 0):.1f}/100")
        print(f"🔢 Total Sessions: {summary.get('total_sessions', 0)}")
        
        # By activity type
        by_type = report.get('by_activity_type', {})
        if by_type:
            print(f"\n📂 Time by Activity Type:")
            print("-" * 40)
            
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
            
            total = summary.get('total_time', 1)
            
            # Sort by time
            sorted_types = sorted(by_type.items(), key=lambda x: x[1]['time'], reverse=True)
            
            for activity_type, data in sorted_types:
                emoji = emoji_map.get(activity_type, '❓')
                time_str = data.get('time_formatted', '0s')
                pct = (data['time'] / total * 100) if total > 0 else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"  {emoji} {activity_type:12} {time_str:>10} {bar} {pct:.1f}%")
        
        # Top apps
        top_apps = report.get('top_apps', [])
        if top_apps:
            print(f"\n🏆 Top Applications:")
            print("-" * 40)
            for i, app in enumerate(top_apps[:5], 1):
                time_str = format_duration(app.get('total_time', 0))
                print(f"  {i}. {app.get('app_name', 'Unknown'):30} {time_str}")
        
        # Top websites
        top_sites = report.get('top_websites', [])
        if top_sites:
            print(f"\n🌐 Top Websites:")
            print("-" * 40)
            for i, site in enumerate(top_sites[:5], 1):
                time_str = format_duration(site.get('total_time', 0))
                print(f"  {i}. {site.get('website', 'Unknown'):30} {time_str}")
        
        print("\n" + "=" * 50 + "\n")
    
    def export_to_json(self, report: Dict[str, Any], filepath: str = None) -> str:
        """Export report to JSON file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/reports/report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Report exported to {filepath}")
        return filepath
    
    def export_to_csv(self, report: Dict[str, Any], filepath: str = None) -> str:
        """Export report to CSV file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/reports/report_{timestamp}.csv"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write summary
            writer.writerow(['Date', report.get('date', '')])
            writer.writerow(['Total Time (seconds)', report.get('summary', {}).get('total_time', 0)])
            writer.writerow(['Productivity Score', report.get('summary', {}).get('productivity_score', 0)])
            writer.writerow([])
            
            # Write activity breakdown
            writer.writerow(['Activity Type', 'Time (seconds)', 'Sessions'])
            for activity_type, data in report.get('by_activity_type', {}).items():
                writer.writerow([activity_type, data['time'], data['count']])
        
        self.logger.info(f"Report exported to {filepath}")
        return filepath
