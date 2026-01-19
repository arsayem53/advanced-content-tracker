"""
Video Detector - Detects and classifies video content types.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class VideoDetector:
    """
    Detects the type of video content being watched.
    Works with window titles, URLs, and OCR text.
    """
    
    # Video content type patterns
    VIDEO_PATTERNS = {
        "cartoon": {
            "keywords": ["cartoon", "animation", "animated", "disney", "pixar", "dreamworks"],
            "title_patterns": [r"cartoon", r"animation"],
            "activity": "entertainment"
        },
        "anime": {
            "keywords": ["anime", "manga", "subbed", "dubbed", "crunchyroll", "funimation", 
                        "isekai", "shonen", "shoujo", "seinen", "episode", "ep\d+"],
            "title_patterns": [r"anime", r"\bep\s*\d+", r"episode\s*\d+", r"sub|dub"],
            "activity": "entertainment"
        },
        "music_video": {
            "keywords": ["official video", "music video", "mv", "official mv", "lyrics", 
                        "official audio", "vevo", "official music"],
            "title_patterns": [r"official\s*(music\s*)?video", r"\(official\)", r"lyrics", r"mv\b"],
            "activity": "entertainment"
        },
        "tutorial": {
            "keywords": ["tutorial", "how to", "learn", "course", "lesson", "guide", 
                        "explained", "for beginners", "step by step", "walkthrough"],
            "title_patterns": [r"tutorial", r"how\s+to", r"learn\s+\w+", r"beginner", r"course"],
            "activity": "educational"
        },
        "gaming": {
            "keywords": ["gameplay", "playthrough", "let's play", "walkthrough", "speedrun",
                        "gaming", "gamer", "twitch", "stream", "esports", "fortnite", 
                        "minecraft", "valorant", "league of legends", "csgo", "cod"],
            "title_patterns": [r"gameplay", r"let'?s?\s*play", r"walkthrough", r"speedrun"],
            "activity": "entertainment"
        },
        "movie": {
            "keywords": ["full movie", "film", "trailer", "cinema", "theatrical"],
            "title_patterns": [r"full\s+movie", r"trailer", r"\(\d{4}\)"],
            "activity": "entertainment"
        },
        "series": {
            "keywords": ["season", "episode", "s0", "e0", "series", "show", "netflix", 
                        "hbo", "streaming"],
            "title_patterns": [r"s\d+e\d+", r"season\s*\d+", r"episode\s*\d+", r"ep\s*\d+"],
            "activity": "entertainment"
        },
        "documentary": {
            "keywords": ["documentary", "nature", "history", "biography", "national geographic",
                        "discovery", "bbc", "planet earth", "investigation"],
            "title_patterns": [r"documentary", r"nat\s*geo", r"discovery"],
            "activity": "educational"
        },
        "news": {
            "keywords": ["news", "breaking", "live news", "report", "headline", 
                        "cnn", "bbc", "fox", "msnbc", "press conference"],
            "title_patterns": [r"news", r"breaking", r"live\s+coverage"],
            "activity": "news"
        },
        "comedy": {
            "keywords": ["comedy", "stand up", "standup", "funny", "comedian", "jokes",
                        "sketch", "parody", "roast", "snl"],
            "title_patterns": [r"stand\s*up", r"comedy", r"funny", r"comedian"],
            "activity": "entertainment"
        },
        "podcast": {
            "keywords": ["podcast", "episode", "interview", "talk show", "discussion"],
            "title_patterns": [r"podcast", r"ep\s*#?\d+", r"interview"],
            "activity": "neutral"
        },
        "sports": {
            "keywords": ["sports", "match", "game", "highlights", "football", "basketball",
                        "soccer", "nfl", "nba", "fifa", "championship", "vs", "versus"],
            "title_patterns": [r"vs\.?", r"match", r"highlights", r"championship"],
            "activity": "entertainment"
        },
        "vlog": {
            "keywords": ["vlog", "daily vlog", "day in my life", "routine", "grwm",
                        "what i eat", "haul", "room tour"],
            "title_patterns": [r"vlog", r"day\s+in\s+my\s+life", r"routine", r"grwm"],
            "activity": "entertainment"
        },
        "asmr": {
            "keywords": ["asmr", "relaxing", "sleep", "tingles", "whisper"],
            "title_patterns": [r"asmr", r"relaxing\s+sounds"],
            "activity": "entertainment"
        },
        "tech_review": {
            "keywords": ["review", "unboxing", "hands on", "first look", "comparison",
                        "vs", "benchmark", "test"],
            "title_patterns": [r"review", r"unboxing", r"hands\s+on", r"benchmark"],
            "activity": "neutral"
        },
        "cooking": {
            "keywords": ["recipe", "cooking", "how to make", "chef", "food", "baking",
                        "kitchen", "meal prep"],
            "title_patterns": [r"recipe", r"how\s+to\s+make", r"cooking"],
            "activity": "neutral"
        },
        "live_stream": {
            "keywords": ["live", "streaming", "stream", "live now", "🔴"],
            "title_patterns": [r"live\s*stream", r"\blive\b", r"streaming"],
            "activity": "entertainment"
        },
        "educational": {
            "keywords": ["explained", "education", "science", "math", "physics", "chemistry",
                        "history", "lecture", "ted talk", "kurzgesagt", "veritasium"],
            "title_patterns": [r"explained", r"lecture", r"ted\s*talk"],
            "activity": "educational"
        },
        "fitness": {
            "keywords": ["workout", "exercise", "fitness", "gym", "yoga", "pilates",
                        "hiit", "cardio", "training"],
            "title_patterns": [r"workout", r"exercise", r"hiit", r"yoga"],
            "activity": "productive"
        },
        "diy": {
            "keywords": ["diy", "craft", "handmade", "project", "build", "make"],
            "title_patterns": [r"\bdiy\b", r"how\s+to\s+build", r"craft"],
            "activity": "productive"
        }
    }
    
    def __init__(self):
        """Initialize video detector."""
        # Compile regex patterns
        self.compiled_patterns = {}
        for video_type, info in self.VIDEO_PATTERNS.items():
            patterns = info.get("title_patterns", [])
            if patterns:
                self.compiled_patterns[video_type] = [
                    re.compile(p, re.IGNORECASE) for p in patterns
                ]
    
    def detect(self, title: str = "", url: str = "", ocr_text: str = "") -> Dict[str, Any]:
        """
        Detect video content type.
        
        Args:
            title: Video/window title
            url: Video URL
            ocr_text: Text extracted from screen via OCR
            
        Returns:
            Dict with detection results
        """
        result = {
            "video_type": "unknown",
            "video_category": "",
            "activity_type": "entertainment",
            "confidence": 0.5,
            "detected_keywords": [],
            "is_live": False,
            "is_educational": False,
            "is_entertainment": True
        }
        
        # Combine all text for analysis
        combined_text = f"{title} {url} {ocr_text}".lower()
        
        if not combined_text.strip():
            return result
        
        # Check for live content
        result["is_live"] = self._check_live(combined_text)
        
        # Score each video type
        scores = {}
        for video_type, info in self.VIDEO_PATTERNS.items():
            score = self._calculate_score(combined_text, info, video_type)
            if score > 0:
                scores[video_type] = score
        
        # Get best match
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            
            result["video_type"] = best_type
            result["video_category"] = best_type
            result["activity_type"] = self.VIDEO_PATTERNS[best_type]["activity"]
            result["confidence"] = min(1.0, best_score / 3.0)  # Normalize score
            result["detected_keywords"] = self._get_matched_keywords(combined_text, best_type)
        
        # Set flags
        result["is_educational"] = result["activity_type"] == "educational"
        result["is_entertainment"] = result["activity_type"] == "entertainment"
        
        return result
    
    def _calculate_score(self, text: str, info: Dict, video_type: str) -> float:
        """Calculate match score for a video type."""
        score = 0.0
        
        # Check keywords
        keywords = info.get("keywords", [])
        for kw in keywords:
            if kw.lower() in text:
                score += 1.0
        
        # Check regex patterns
        if video_type in self.compiled_patterns:
            for pattern in self.compiled_patterns[video_type]:
                if pattern.search(text):
                    score += 1.5  # Regex matches are weighted higher
        
        return score
    
    def _check_live(self, text: str) -> bool:
        """Check if content is live streaming."""
        live_indicators = ["🔴", "live", "streaming now", "live stream", "live now"]
        return any(indicator in text for indicator in live_indicators)
    
    def _get_matched_keywords(self, text: str, video_type: str) -> List[str]:
        """Get list of keywords that matched."""
        matched = []
        keywords = self.VIDEO_PATTERNS.get(video_type, {}).get("keywords", [])
        for kw in keywords:
            if kw.lower() in text:
                matched.append(kw)
        return matched[:5]  # Limit to 5 keywords
    
    def get_video_description(self, detection: Dict, title: str = "") -> str:
        """Generate human-readable description of video content."""
        video_type = detection.get("video_type", "unknown")
        is_live = detection.get("is_live", False)
        
        if video_type == "unknown":
            if title:
                return f"Watching: {title[:50]}"
            return "Watching video"
        
        # Format video type nicely
        type_display = video_type.replace("_", " ").title()
        
        if is_live:
            return f"Watching live: {type_display}"
        
        return f"Watching: {type_display}"
    
    def is_educational_video(self, title: str = "", url: str = "") -> bool:
        """Quick check if video appears educational."""
        detection = self.detect(title, url)
        return detection.get("is_educational", False)
    
    def is_entertainment_video(self, title: str = "", url: str = "") -> bool:
        """Quick check if video appears to be entertainment."""
        detection = self.detect(title, url)
        return detection.get("is_entertainment", True)
