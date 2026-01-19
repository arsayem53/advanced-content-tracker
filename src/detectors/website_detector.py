"""
Website Detector - Detects and classifies websites.
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebsiteDetector:
    """
    Detects what website is being visited and classifies it.
    """
    
    # Default website classifications
    DEFAULT_WEBSITE_RULES = {
        # Video Streaming
        "youtube.com": {"category": "video_streaming", "activity": "entertainment", "name": "YouTube"},
        "youtu.be": {"category": "video_streaming", "activity": "entertainment", "name": "YouTube"},
        "netflix.com": {"category": "video_streaming", "activity": "entertainment", "name": "Netflix"},
        "primevideo.com": {"category": "video_streaming", "activity": "entertainment", "name": "Prime Video"},
        "amazon.com/prime": {"category": "video_streaming", "activity": "entertainment", "name": "Prime Video"},
        "disneyplus.com": {"category": "video_streaming", "activity": "entertainment", "name": "Disney+"},
        "hulu.com": {"category": "video_streaming", "activity": "entertainment", "name": "Hulu"},
        "hbomax.com": {"category": "video_streaming", "activity": "entertainment", "name": "HBO Max"},
        "max.com": {"category": "video_streaming", "activity": "entertainment", "name": "Max"},
        "twitch.tv": {"category": "live_streaming", "activity": "entertainment", "name": "Twitch"},
        "vimeo.com": {"category": "video_streaming", "activity": "neutral", "name": "Vimeo"},
        "dailymotion.com": {"category": "video_streaming", "activity": "entertainment", "name": "Dailymotion"},
        "crunchyroll.com": {"category": "anime_streaming", "activity": "entertainment", "name": "Crunchyroll"},
        "funimation.com": {"category": "anime_streaming", "activity": "entertainment", "name": "Funimation"},
        
        # Social Media
        "facebook.com": {"category": "social_media", "activity": "social_media", "name": "Facebook"},
        "fb.com": {"category": "social_media", "activity": "social_media", "name": "Facebook"},
        "instagram.com": {"category": "social_media", "activity": "social_media", "name": "Instagram"},
        "twitter.com": {"category": "social_media", "activity": "social_media", "name": "Twitter"},
        "x.com": {"category": "social_media", "activity": "social_media", "name": "X (Twitter)"},
        "tiktok.com": {"category": "social_media", "activity": "social_media", "name": "TikTok"},
        "snapchat.com": {"category": "social_media", "activity": "social_media", "name": "Snapchat"},
        "pinterest.com": {"category": "social_media", "activity": "social_media", "name": "Pinterest"},
        "tumblr.com": {"category": "social_media", "activity": "social_media", "name": "Tumblr"},
        
        # Professional Networking
        "linkedin.com": {"category": "professional", "activity": "productive", "name": "LinkedIn"},
        
        # Reddit & Forums
        "reddit.com": {"category": "forum", "activity": "social_media", "name": "Reddit"},
        "old.reddit.com": {"category": "forum", "activity": "social_media", "name": "Reddit"},
        "quora.com": {"category": "forum", "activity": "neutral", "name": "Quora"},
        "news.ycombinator.com": {"category": "tech_forum", "activity": "educational", "name": "Hacker News"},
        "slashdot.org": {"category": "tech_forum", "activity": "educational", "name": "Slashdot"},
        
        # Development & Coding
        "github.com": {"category": "development", "activity": "productive", "name": "GitHub"},
        "gitlab.com": {"category": "development", "activity": "productive", "name": "GitLab"},
        "bitbucket.org": {"category": "development", "activity": "productive", "name": "Bitbucket"},
        "stackoverflow.com": {"category": "development", "activity": "productive", "name": "Stack Overflow"},
        "stackexchange.com": {"category": "development", "activity": "productive", "name": "Stack Exchange"},
        "developer.mozilla.org": {"category": "documentation", "activity": "educational", "name": "MDN"},
        "devdocs.io": {"category": "documentation", "activity": "educational", "name": "DevDocs"},
        "docs.python.org": {"category": "documentation", "activity": "educational", "name": "Python Docs"},
        "docs.microsoft.com": {"category": "documentation", "activity": "educational", "name": "Microsoft Docs"},
        "learn.microsoft.com": {"category": "documentation", "activity": "educational", "name": "Microsoft Learn"},
        "npmjs.com": {"category": "development", "activity": "productive", "name": "npm"},
        "pypi.org": {"category": "development", "activity": "productive", "name": "PyPI"},
        "crates.io": {"category": "development", "activity": "productive", "name": "crates.io"},
        "hub.docker.com": {"category": "development", "activity": "productive", "name": "Docker Hub"},
        "codepen.io": {"category": "development", "activity": "productive", "name": "CodePen"},
        "jsfiddle.net": {"category": "development", "activity": "productive", "name": "JSFiddle"},
        "replit.com": {"category": "development", "activity": "productive", "name": "Replit"},
        "codesandbox.io": {"category": "development", "activity": "productive", "name": "CodeSandbox"},
        
        # Learning Platforms
        "udemy.com": {"category": "learning", "activity": "educational", "name": "Udemy"},
        "coursera.org": {"category": "learning", "activity": "educational", "name": "Coursera"},
        "edx.org": {"category": "learning", "activity": "educational", "name": "edX"},
        "khanacademy.org": {"category": "learning", "activity": "educational", "name": "Khan Academy"},
        "pluralsight.com": {"category": "learning", "activity": "educational", "name": "Pluralsight"},
        "skillshare.com": {"category": "learning", "activity": "educational", "name": "Skillshare"},
        "linkedin.com/learning": {"category": "learning", "activity": "educational", "name": "LinkedIn Learning"},
        "codecademy.com": {"category": "learning", "activity": "educational", "name": "Codecademy"},
        "freecodecamp.org": {"category": "learning", "activity": "educational", "name": "freeCodeCamp"},
        "leetcode.com": {"category": "learning", "activity": "educational", "name": "LeetCode"},
        "hackerrank.com": {"category": "learning", "activity": "educational", "name": "HackerRank"},
        "codewars.com": {"category": "learning", "activity": "educational", "name": "Codewars"},
        
        # Tech News & Blogs
        "medium.com": {"category": "blog", "activity": "neutral", "name": "Medium"},
        "dev.to": {"category": "tech_blog", "activity": "educational", "name": "DEV Community"},
        "hashnode.com": {"category": "tech_blog", "activity": "educational", "name": "Hashnode"},
        "techcrunch.com": {"category": "tech_news", "activity": "news", "name": "TechCrunch"},
        "theverge.com": {"category": "tech_news", "activity": "news", "name": "The Verge"},
        "arstechnica.com": {"category": "tech_news", "activity": "news", "name": "Ars Technica"},
        "wired.com": {"category": "tech_news", "activity": "news", "name": "Wired"},
        
        # News Sites
        "bbc.com": {"category": "news", "activity": "news", "name": "BBC"},
        "cnn.com": {"category": "news", "activity": "news", "name": "CNN"},
        "nytimes.com": {"category": "news", "activity": "news", "name": "NY Times"},
        "theguardian.com": {"category": "news", "activity": "news", "name": "The Guardian"},
        "reuters.com": {"category": "news", "activity": "news", "name": "Reuters"},
        "apnews.com": {"category": "news", "activity": "news", "name": "AP News"},
        "news.google.com": {"category": "news", "activity": "news", "name": "Google News"},
        
        # Shopping
        "amazon.com": {"category": "shopping", "activity": "shopping", "name": "Amazon"},
        "amazon.co.uk": {"category": "shopping", "activity": "shopping", "name": "Amazon UK"},
        "ebay.com": {"category": "shopping", "activity": "shopping", "name": "eBay"},
        "aliexpress.com": {"category": "shopping", "activity": "shopping", "name": "AliExpress"},
        "walmart.com": {"category": "shopping", "activity": "shopping", "name": "Walmart"},
        "target.com": {"category": "shopping", "activity": "shopping", "name": "Target"},
        "etsy.com": {"category": "shopping", "activity": "shopping", "name": "Etsy"},
        
        # Music
        "spotify.com": {"category": "music", "activity": "entertainment", "name": "Spotify"},
        "open.spotify.com": {"category": "music", "activity": "entertainment", "name": "Spotify"},
        "music.apple.com": {"category": "music", "activity": "entertainment", "name": "Apple Music"},
        "soundcloud.com": {"category": "music", "activity": "entertainment", "name": "SoundCloud"},
        "pandora.com": {"category": "music", "activity": "entertainment", "name": "Pandora"},
        "deezer.com": {"category": "music", "activity": "entertainment", "name": "Deezer"},
        "bandcamp.com": {"category": "music", "activity": "entertainment", "name": "Bandcamp"},
        
        # Productivity Tools
        "notion.so": {"category": "productivity", "activity": "productive", "name": "Notion"},
        "trello.com": {"category": "productivity", "activity": "productive", "name": "Trello"},
        "asana.com": {"category": "productivity", "activity": "productive", "name": "Asana"},
        "monday.com": {"category": "productivity", "activity": "productive", "name": "Monday"},
        "airtable.com": {"category": "productivity", "activity": "productive", "name": "Airtable"},
        "docs.google.com": {"category": "productivity", "activity": "productive", "name": "Google Docs"},
        "sheets.google.com": {"category": "productivity", "activity": "productive", "name": "Google Sheets"},
        "slides.google.com": {"category": "productivity", "activity": "productive", "name": "Google Slides"},
        "drive.google.com": {"category": "cloud_storage", "activity": "productive", "name": "Google Drive"},
        "dropbox.com": {"category": "cloud_storage", "activity": "productive", "name": "Dropbox"},
        "onedrive.live.com": {"category": "cloud_storage", "activity": "productive", "name": "OneDrive"},
        "figma.com": {"category": "design", "activity": "productive", "name": "Figma"},
        "canva.com": {"category": "design", "activity": "productive", "name": "Canva"},
        "miro.com": {"category": "collaboration", "activity": "productive", "name": "Miro"},
        
        # Email
        "mail.google.com": {"category": "email", "activity": "productive", "name": "Gmail"},
        "outlook.live.com": {"category": "email", "activity": "productive", "name": "Outlook"},
        "outlook.office.com": {"category": "email", "activity": "productive", "name": "Outlook"},
        "mail.yahoo.com": {"category": "email", "activity": "productive", "name": "Yahoo Mail"},
        "protonmail.com": {"category": "email", "activity": "productive", "name": "ProtonMail"},
        "proton.me": {"category": "email", "activity": "productive", "name": "Proton Mail"},
        
        # Search Engines
        "google.com": {"category": "search", "activity": "neutral", "name": "Google"},
        "bing.com": {"category": "search", "activity": "neutral", "name": "Bing"},
        "duckduckgo.com": {"category": "search", "activity": "neutral", "name": "DuckDuckGo"},
        
        # Gaming
        "store.steampowered.com": {"category": "gaming", "activity": "gaming", "name": "Steam Store"},
        "epicgames.com": {"category": "gaming", "activity": "gaming", "name": "Epic Games"},
        "gog.com": {"category": "gaming", "activity": "gaming", "name": "GOG"},
        "itch.io": {"category": "gaming", "activity": "gaming", "name": "itch.io"},
        
        # AI Tools
        "chat.openai.com": {"category": "ai_tool", "activity": "productive", "name": "ChatGPT"},
        "openai.com": {"category": "ai_tool", "activity": "productive", "name": "OpenAI"},
        "claude.ai": {"category": "ai_tool", "activity": "productive", "name": "Claude"},
        "bard.google.com": {"category": "ai_tool", "activity": "productive", "name": "Google Bard"},
        "gemini.google.com": {"category": "ai_tool", "activity": "productive", "name": "Google Gemini"},
        "copilot.github.com": {"category": "ai_tool", "activity": "productive", "name": "GitHub Copilot"},
        "midjourney.com": {"category": "ai_tool", "activity": "productive", "name": "Midjourney"},
        "huggingface.co": {"category": "ai_tool", "activity": "productive", "name": "Hugging Face"},
        
        # Adult Content (generic patterns)
        "pornhub.com": {"category": "adult", "activity": "adult", "name": "Adult Site", "nsfw": True},
        "xvideos.com": {"category": "adult", "activity": "adult", "name": "Adult Site", "nsfw": True},
        "xnxx.com": {"category": "adult", "activity": "adult", "name": "Adult Site", "nsfw": True},
        "xhamster.com": {"category": "adult", "activity": "adult", "name": "Adult Site", "nsfw": True},
        "redtube.com": {"category": "adult", "activity": "adult", "name": "Adult Site", "nsfw": True},
    }
    
    # Patterns for detecting adult content
    ADULT_PATTERNS = [
        r'porn', r'xxx', r'adult', r'nsfw', r'18\+', r'erotic',
        r'nude', r'naked', r'sex', r'hentai'
    ]
    
    def __init__(self, rules_path: str = None):
        """
        Initialize website detector.
        
        Args:
            rules_path: Path to custom rules JSON file
        """
        self.rules = self.DEFAULT_WEBSITE_RULES.copy()
        
        # Compile adult patterns
        self.adult_regex = re.compile('|'.join(self.ADULT_PATTERNS), re.IGNORECASE)
        
        # Load custom rules if provided
        if rules_path and os.path.exists(rules_path):
            try:
                with open(rules_path, 'r') as f:
                    custom_rules = json.load(f)
                self.rules.update(custom_rules)
                logger.info(f"Loaded {len(custom_rules)} custom website rules")
            except Exception as e:
                logger.error(f"Failed to load custom website rules: {e}")
    
    def detect(self, url: str, window_title: str = "") -> Dict[str, Any]:
        """
        Detect and classify a website.
        
        Args:
            url: Website URL or domain
            window_title: Browser window title
            
        Returns:
            Dict with detection results
        """
        result = {
            "website": "",
            "domain": "",
            "category": "unknown",
            "activity_type": "neutral",
            "name": "",
            "is_nsfw": False,
            "is_video_site": False,
            "is_social_media": False,
            "is_shopping": False,
            "is_educational": False,
            "confidence": 0.5
        }
        
        if not url and not window_title:
            return result
        
        # Extract domain from URL
        domain = self._extract_domain(url)
        result["domain"] = domain
        result["website"] = domain
        
        # Try to match domain against rules
        matched = False
        for pattern, info in self.rules.items():
            if pattern in domain or pattern in url.lower():
                result["category"] = info.get("category", "unknown")
                result["activity_type"] = info.get("activity", "neutral")
                result["name"] = info.get("name", domain)
                result["is_nsfw"] = info.get("nsfw", False)
                result["confidence"] = 0.9
                matched = True
                break
        
        # If no match, try to detect from window title
        if not matched and window_title:
            result = self._detect_from_title(result, window_title)
        
        # Check for adult content patterns
        if not result["is_nsfw"]:
            result["is_nsfw"] = self._check_adult_content(url, window_title, domain)
        
        # Set boolean flags
        result["is_video_site"] = result["category"] in ["video_streaming", "live_streaming", "anime_streaming"]
        result["is_social_media"] = result["category"] in ["social_media", "forum"]
        result["is_shopping"] = result["category"] == "shopping"
        result["is_educational"] = result["category"] in ["learning", "documentation", "tech_blog"]
        
        return result
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ""
        
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
            return url.lower()
    
    def _detect_from_title(self, result: Dict, title: str) -> Dict:
        """Try to detect website from browser title."""
        title_lower = title.lower()
        
        # Common title patterns
        title_patterns = {
            "youtube": {"category": "video_streaming", "activity": "entertainment", "name": "YouTube"},
            "github": {"category": "development", "activity": "productive", "name": "GitHub"},
            "stack overflow": {"category": "development", "activity": "productive", "name": "Stack Overflow"},
            "reddit": {"category": "forum", "activity": "social_media", "name": "Reddit"},
            "twitter": {"category": "social_media", "activity": "social_media", "name": "Twitter"},
            "facebook": {"category": "social_media", "activity": "social_media", "name": "Facebook"},
            "instagram": {"category": "social_media", "activity": "social_media", "name": "Instagram"},
            "linkedin": {"category": "professional", "activity": "productive", "name": "LinkedIn"},
            "netflix": {"category": "video_streaming", "activity": "entertainment", "name": "Netflix"},
            "amazon": {"category": "shopping", "activity": "shopping", "name": "Amazon"},
            "gmail": {"category": "email", "activity": "productive", "name": "Gmail"},
            "google docs": {"category": "productivity", "activity": "productive", "name": "Google Docs"},
        }
        
        for pattern, info in title_patterns.items():
            if pattern in title_lower:
                result["category"] = info["category"]
                result["activity_type"] = info["activity"]
                result["name"] = info["name"]
                result["confidence"] = 0.7
                break
        
        return result
    
    def _check_adult_content(self, url: str, title: str, domain: str) -> bool:
        """Check if content appears to be adult/NSFW."""
        combined = f"{url} {title} {domain}".lower()
        return bool(self.adult_regex.search(combined))
    
    def is_productive_site(self, url: str) -> bool:
        """Quick check if website is considered productive."""
        detection = self.detect(url)
        return detection["activity_type"] in ["productive", "educational"]
    
    def is_distracting_site(self, url: str) -> bool:
        """Quick check if website is considered distracting."""
        detection = self.detect(url)
        return detection["activity_type"] in ["entertainment", "social_media", "gaming", "adult"]
    
    def get_website_category(self, url: str) -> str:
        """Get category for a website."""
        detection = self.detect(url)
        return detection["category"]
