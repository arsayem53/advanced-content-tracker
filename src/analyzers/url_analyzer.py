"""
URL Analyzer - Detects and classifies websites.
"""

import re
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class URLAnalyzer:
    """
    Analyzes URLs to determine content type and activity.
    """
    
    # Website classifications
    SITE_RULES = {
        # Video Streaming
        'youtube.com': {'category': 'video_streaming', 'activity': 'entertainment', 'name': 'YouTube'},
        'youtu.be': {'category': 'video_streaming', 'activity': 'entertainment', 'name': 'YouTube'},
        'netflix.com': {'category': 'video_streaming', 'activity': 'entertainment', 'name': 'Netflix'},
        'twitch.tv': {'category': 'live_streaming', 'activity': 'entertainment', 'name': 'Twitch'},
        'vimeo.com': {'category': 'video_streaming', 'activity': 'neutral', 'name': 'Vimeo'},
        
        # Social Media
        'facebook.com': {'category': 'social_media', 'activity': 'social_media', 'name': 'Facebook'},
        'twitter.com': {'category': 'social_media', 'activity': 'social_media', 'name': 'Twitter'},
        'x.com': {'category': 'social_media', 'activity': 'social_media', 'name': 'X'},
        'instagram.com': {'category': 'social_media', 'activity': 'social_media', 'name': 'Instagram'},
        'tiktok.com': {'category': 'social_media', 'activity': 'social_media', 'name': 'TikTok'},
        'reddit.com': {'category': 'forum', 'activity': 'social_media', 'name': 'Reddit'},
        'linkedin.com': {'category': 'professional', 'activity': 'productive', 'name': 'LinkedIn'},
        
        # Development
        'github.com': {'category': 'development', 'activity': 'productive', 'name': 'GitHub'},
        'gitlab.com': {'category': 'development', 'activity': 'productive', 'name': 'GitLab'},
        'stackoverflow.com': {'category': 'development', 'activity': 'productive', 'name': 'Stack Overflow'},
        'developer.mozilla.org': {'category': 'documentation', 'activity': 'educational', 'name': 'MDN'},
        
        # Learning
        'udemy.com': {'category': 'learning', 'activity': 'educational', 'name': 'Udemy'},
        'coursera.org': {'category': 'learning', 'activity': 'educational', 'name': 'Coursera'},
        'khanacademy.org': {'category': 'learning', 'activity': 'educational', 'name': 'Khan Academy'},
        
        # Shopping
        'amazon.com': {'category': 'shopping', 'activity': 'shopping', 'name': 'Amazon'},
        'ebay.com': {'category': 'shopping', 'activity': 'shopping', 'name': 'eBay'},
        
        # News
        'bbc.com': {'category': 'news', 'activity': 'news', 'name': 'BBC'},
        'cnn.com': {'category': 'news', 'activity': 'news', 'name': 'CNN'},
        
        # Productivity
        'docs.google.com': {'category': 'productivity', 'activity': 'productive', 'name': 'Google Docs'},
        'notion.so': {'category': 'productivity', 'activity': 'productive', 'name': 'Notion'},
        'trello.com': {'category': 'productivity', 'activity': 'productive', 'name': 'Trello'},
        
        # Email
        'mail.google.com': {'category': 'email', 'activity': 'productive', 'name': 'Gmail'},
        'outlook.live.com': {'category': 'email', 'activity': 'productive', 'name': 'Outlook'},
    }
    
    def __init__(self):
        """Initialize URL Analyzer."""
        self.logger = logging.getLogger("URLAnalyzer")
    
    def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyze a URL and return classification.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dict with analysis results
        """
        if not url:
            return {}
        
        result = {
            'url': url,
            'domain': '',
            'website': '',
            'content_type': 'other',
            'activity': 'neutral',
            'name': '',
        }
        
        # Extract domain
        domain = self._extract_domain(url)
        result['domain'] = domain
        result['website'] = domain
        
        # Match against known sites
        for site_domain, info in self.SITE_RULES.items():
            if site_domain in domain:
                result['content_type'] = info['category']
                result['activity'] = info['activity']
                result['name'] = info['name']
                break
        
        # Extract video ID if YouTube
        if 'youtube.com' in domain or 'youtu.be' in domain:
            video_id = self._extract_youtube_id(url)
            if video_id:
                result['video_id'] = video_id
        
        return result
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ''
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www.
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Remove port
            if ':' in domain:
                domain = domain.split(':')[0]
            
            return domain
        except Exception:
            return ''
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def simple_classify(self, url: str) -> str:
        """Quick classification returning activity type."""
        result = self.analyze(url)
        return result.get('activity', 'neutral')
