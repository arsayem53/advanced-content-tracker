"""
Activity Detector - High-level activity classification.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .app_detector import AppDetector
from .website_detector import WebsiteDetector
from .video_detector import VideoDetector

logger = logging.getLogger(__name__)


@dataclass
class ActivityResult:
    """Result of activity detection."""
    activity_type: str  # productive, educational, entertainment, social_media, etc.
    category: str       # coding, video, social_feed, etc.
    description: str    # Human-readable description
    is_productive: bool
    productivity_score: float  # -1.0 to 1.0
    confidence: float   # 0.0 to 1.0
    is_nsfw: bool = False
    is_idle: bool = False


class ActivityDetector:
    """
    High-level activity detection combining all detection methods.
    Determines whether user is being productive, learning, or wasting time.
    """
    
    # Productivity weights for different activity types
    PRODUCTIVITY_WEIGHTS = {
        "productive": 1.0,
        "educational": 0.8,
        "neutral": 0.0,
        "news": -0.1,
        "shopping": -0.2,
        "entertainment": -0.3,
        "social_media": -0.4,
        "gaming": -0.3,
        "adult": -1.0,
        "idle": 0.0
    }
    
    def __init__(self):
        """Initialize activity detector with sub-detectors."""
        self.app_detector = AppDetector()
        self.website_detector = WebsiteDetector()
        self.video_detector = VideoDetector()
        
        logger.info("ActivityDetector initialized")
    
    def detect(
        self,
        app_name: str = "",
        process_name: str = "",
        window_title: str = "",
        url: str = "",
        wm_class: str = "",
        ocr_text: str = "",
        is_browser: bool = False
    ) -> ActivityResult:
        """
        Detect current activity and classify it.
        
        Args:
            app_name: Application name
            process_name: Process name
            window_title: Window title
            url: Current URL (if browser)
            wm_class: Window manager class
            ocr_text: OCR extracted text
            is_browser: Whether the active app is a browser
            
        Returns:
            ActivityResult with classification
        """
        # Start with default result
        result = ActivityResult(
            activity_type="neutral",
            category="unknown",
            description="",
            is_productive=False,
            productivity_score=0.0,
            confidence=0.5,
            is_nsfw=False,
            is_idle=False
        )
        
        # Detect app type
        app_detection = self.app_detector.detect(process_name, wm_class, window_title)
        
        # If it's a browser, analyze website
        if is_browser or app_detection.get("is_browser", False):
            result = self._analyze_browser_activity(url, window_title, ocr_text)
        
        # If it's a media player, analyze video content
        elif app_detection.get("is_media_player", False):
            result = self._analyze_media_activity(window_title, ocr_text)
        
        # If it's an IDE/terminal, mark as productive
        elif app_detection.get("is_ide", False) or app_detection.get("is_terminal", False):
            result = self._create_coding_result(app_detection, window_title)
        
        # If it's a game, mark as gaming
        elif app_detection.get("is_game", False):
            result = self._create_gaming_result(app_detection, window_title)
        
        # Otherwise, use app detection
        else:
            result = self._create_app_result(app_detection, window_title)
        
        return result
    
    def _analyze_browser_activity(
        self,
        url: str,
        window_title: str,
        ocr_text: str
    ) -> ActivityResult:
        """Analyze browser activity."""
        # Detect website
        website_detection = self.website_detector.detect(url, window_title)
        
        # Check if it's a video site
        if website_detection.get("is_video_site", False):
            video_detection = self.video_detector.detect(window_title, url, ocr_text)
            
            activity_type = video_detection.get("activity_type", "entertainment")
            video_type = video_detection.get("video_type", "unknown")
            
            description = self.video_detector.get_video_description(video_detection, window_title)
            
            return ActivityResult(
                activity_type=activity_type,
                category=f"video_{video_type}",
                description=description,
                is_productive=activity_type in ["educational", "productive"],
                productivity_score=self.PRODUCTIVITY_WEIGHTS.get(activity_type, 0.0),
                confidence=video_detection.get("confidence", 0.5),
                is_nsfw=website_detection.get("is_nsfw", False)
            )
        
        # Regular website
        activity_type = website_detection.get("activity_type", "neutral")
        category = website_detection.get("category", "browsing")
        site_name = website_detection.get("name", website_detection.get("domain", "Website"))
        
        # Generate description
        if activity_type == "productive":
            description = f"Working on {site_name}"
        elif activity_type == "educational":
            description = f"Learning on {site_name}"
        elif activity_type == "social_media":
            description = f"Browsing {site_name}"
        elif activity_type == "entertainment":
            description = f"Entertainment on {site_name}"
        elif activity_type == "shopping":
            description = f"Shopping on {site_name}"
        else:
            description = f"Browsing {site_name}"
        
        return ActivityResult(
            activity_type=activity_type,
            category=category,
            description=description,
            is_productive=activity_type in ["productive", "educational"],
            productivity_score=self.PRODUCTIVITY_WEIGHTS.get(activity_type, 0.0),
            confidence=website_detection.get("confidence", 0.5),
            is_nsfw=website_detection.get("is_nsfw", False)
        )
    
    def _analyze_media_activity(
        self,
        window_title: str,
        ocr_text: str
    ) -> ActivityResult:
        """Analyze media player activity."""
        video_detection = self.video_detector.detect(window_title, "", ocr_text)
        
        activity_type = video_detection.get("activity_type", "entertainment")
        video_type = video_detection.get("video_type", "video")
        
        description = self.video_detector.get_video_description(video_detection, window_title)
        
        return ActivityResult(
            activity_type=activity_type,
            category=f"local_video_{video_type}",
            description=description,
            is_productive=activity_type in ["educational", "productive"],
            productivity_score=self.PRODUCTIVITY_WEIGHTS.get(activity_type, -0.3),
            confidence=video_detection.get("confidence", 0.5)
        )
    
    def _create_coding_result(
        self,
        app_detection: Dict,
        window_title: str
    ) -> ActivityResult:
        """Create result for coding activity."""
        app_name = app_detection.get("app_name", "IDE")
        
        # Try to detect programming language from title
        lang = self._detect_programming_language(window_title)
        if lang:
            description = f"Coding {lang} in {app_name}"
        else:
            description = f"Coding in {app_name}"
        
        return ActivityResult(
            activity_type="productive",
            category="coding",
            description=description,
            is_productive=True,
            productivity_score=1.0,
            confidence=0.9
        )
    
    def _create_gaming_result(
        self,
        app_detection: Dict,
        window_title: str
    ) -> ActivityResult:
        """Create result for gaming activity."""
        app_name = app_detection.get("app_name", "Game")
        
        return ActivityResult(
            activity_type="gaming",
            category="gaming",
            description=f"Playing {app_name}",
            is_productive=False,
            productivity_score=self.PRODUCTIVITY_WEIGHTS["gaming"],
            confidence=0.9
        )
    
    def _create_app_result(
        self,
        app_detection: Dict,
        window_title: str
    ) -> ActivityResult:
        """Create result for general app activity."""
        app_name = app_detection.get("app_name", "Application")
        category = app_detection.get("category", "unknown")
        activity_type = app_detection.get("activity_type", "neutral")
        
        # Generate description based on category
        if category == "email":
            description = f"Reading email in {app_name}"
        elif category == "document":
            description = f"Working on document in {app_name}"
        elif category == "spreadsheet":
            description = f"Working on spreadsheet in {app_name}"
        elif category == "presentation":
            description = f"Working on presentation in {app_name}"
        elif category == "communication":
            description = f"Messaging in {app_name}"
        elif category == "notes":
            description = f"Taking notes in {app_name}"
        elif category == "design":
            description = f"Designing in {app_name}"
        else:
            description = f"Using {app_name}"
        
        return ActivityResult(
            activity_type=activity_type,
            category=category,
            description=description,
            is_productive=activity_type in ["productive", "educational"],
            productivity_score=self.PRODUCTIVITY_WEIGHTS.get(activity_type, 0.0),
            confidence=app_detection.get("confidence", 0.5)
        )
    
    def _detect_programming_language(self, title: str) -> Optional[str]:
        """Detect programming language from window title."""
        title_lower = title.lower()
        
        lang_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.sql': 'SQL',
            '.html': 'HTML',
            '.css': 'CSS',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
        }
        
        for ext, lang in lang_extensions.items():
            if ext in title_lower:
                return lang
        
        return None
    
    def calculate_productivity_score(self, activity_type: str) -> float:
        """Calculate productivity score for an activity type."""
        return self.PRODUCTIVITY_WEIGHTS.get(activity_type, 0.0)
    
    def is_distracting(self, activity_type: str) -> bool:
        """Check if activity type is considered distracting."""
        return activity_type in ["entertainment", "social_media", "gaming", "adult"]
    
    def get_activity_summary(self, result: ActivityResult) -> str:
        """Get a one-line summary of the activity."""
        if result.is_idle:
            return "Idle"
        
        emoji_map = {
            "productive": "💻",
            "educational": "📖",
            "entertainment": "🎬",
            "social_media": "📱",
            "gaming": "🎮",
            "shopping": "🛒",
            "news": "📰",
            "adult": "🔞",
            "neutral": "⚪"
        }
        
        emoji = emoji_map.get(result.activity_type, "❓")
        return f"{emoji} {result.description}"
