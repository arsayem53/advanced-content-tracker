"""
Content Classifier - Main orchestrator that combines all analyzers.
"""

import logging
import time
from typing import Dict, Any, Optional

from .url_analyzer import URLAnalyzer
from .ocr_analyzer import OCRAnalyzer
from .image_analyzer import ImageAnalyzer
from .clip_analyzer import CLIPAnalyzer
from .nsfw_detector import NSFWDetector

logger = logging.getLogger(__name__)


class ContentClassifier:
    """
    Orchestrates all detection methods to classify content.
    Implements the multi-method detection flow.
    """
    
    def __init__(self):
        """Initialize Content Classifier."""
        self.logger = logging.getLogger("ContentClassifier")
        
        # Initialize analyzers (lazy loading for heavy ones)
        self.url_analyzer = URLAnalyzer()
        self.ocr_analyzer = OCRAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        self._clip_analyzer = None
        self._nsfw_detector = None
        
        self.logger.info("ContentClassifier initialized")
    
    @property
    def clip_analyzer(self):
        """Lazy load CLIP analyzer."""
        if self._clip_analyzer is None:
            self._clip_analyzer = CLIPAnalyzer()
        return self._clip_analyzer
    
    @property
    def nsfw_detector(self):
        """Lazy load NSFW detector."""
        if self._nsfw_detector is None:
            self._nsfw_detector = NSFWDetector()
        return self._nsfw_detector
    
    def classify(self, screenshot, window_info=None) -> Dict[str, Any]:
        """
        Main classification entry point.
        
        Args:
            screenshot: PIL Image from screenshot capture
            window_info: Active window information
            
        Returns:
            Dict with classification results
        """
        start_time = time.time()
        
        result = {
            'content_type': 'unknown',
            'content_category': '',
            'content_description': '',
            'content_title': '',
            'activity_type': 'neutral',
            'is_productive': False,
            'productivity_score': 0.0,
            'detection_method': 'rules',
            'confidence': 0.0,
            'nsfw_score': 0.0,
            'is_nsfw': False,
            'extracted_text': '',
        }
        
        # Get window info attributes safely
        app_name = getattr(window_info, 'app_name', '') if window_info else ''
        window_title = getattr(window_info, 'window_title', '') if window_info else ''
        url = getattr(window_info, 'url', '') if window_info else ''
        is_browser = getattr(window_info, 'is_browser', False) if window_info else False
        
        try:
            # Step 1: URL Analysis (if browser)
            if url:
                url_result = self.url_analyzer.analyze(url)
                if url_result:
                    self._merge_url_result(result, url_result)
            
            # Step 2: OCR Analysis
            if screenshot:
                ocr_text = self.ocr_analyzer.extract_text(screenshot)
                if ocr_text:
                    result['extracted_text'] = ocr_text[:500]
                    ocr_result = self.ocr_analyzer.analyze_text(ocr_text)
                    self._merge_ocr_result(result, ocr_result)
            
            # Step 3: Image Analysis
            if screenshot:
                img_result = self.image_analyzer.analyze_image(screenshot)
                self._merge_image_result(result, img_result)
            
            # Step 4: CLIP Classification (if enabled and screenshot available)
            if screenshot:
                try:
                    clip_result = self.clip_analyzer.classify(screenshot)
                    if clip_result.get('confidence', 0) > 0.3:
                        self._merge_clip_result(result, clip_result)
                except Exception as e:
                    self.logger.debug(f"CLIP classification skipped: {e}")
            
            # Step 5: NSFW Detection
            if screenshot:
                try:
                    nsfw_result = self.nsfw_detector.detect(screenshot)
                    result['nsfw_score'] = nsfw_result.get('nsfw_score', 0.0)
                    result['is_nsfw'] = nsfw_result.get('is_nsfw', False)
                    
                    if result['is_nsfw']:
                        result['activity_type'] = 'adult'
                        result['content_category'] = 'adult_content'
                except Exception as e:
                    self.logger.debug(f"NSFW detection skipped: {e}")
            
            # Step 6: Rule-based classification from window info
            self._apply_rules(result, app_name, window_title, is_browser)
            
            # Calculate final productivity score
            result['productivity_score'] = self._calculate_productivity(result['activity_type'])
            result['is_productive'] = result['productivity_score'] > 0
            
            # Generate description if not set
            if not result['content_description']:
                result['content_description'] = self._generate_description(result, app_name, window_title)
            
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
        
        elapsed = (time.time() - start_time) * 1000
        self.logger.debug(f"Classification completed in {elapsed:.1f}ms")
        
        return result
    
    def _merge_url_result(self, result: Dict, url_result: Dict):
        """Merge URL analysis results."""
        if url_result.get('website'):
            result['content_type'] = 'browser'
            
        if url_result.get('content_type'):
            result['content_category'] = url_result['content_type']
            
        if url_result.get('activity'):
            result['activity_type'] = url_result['activity']
            result['confidence'] = max(result['confidence'], 0.7)
    
    def _merge_ocr_result(self, result: Dict, ocr_result: Dict):
        """Merge OCR analysis results."""
        if ocr_result.get('programming_language'):
            result['content_type'] = 'code'
            result['content_category'] = f"coding_{ocr_result['programming_language']}"
            result['activity_type'] = 'productive'
            result['confidence'] = max(result['confidence'], 0.8)
        
        if ocr_result.get('content_suggestions'):
            suggestions = ocr_result['content_suggestions']
            if 'tutorial' in suggestions:
                result['activity_type'] = 'educational'
            elif 'entertainment' in suggestions:
                result['activity_type'] = 'entertainment'
    
    def _merge_image_result(self, result: Dict, img_result: Dict):
        """Merge image analysis results."""
        # Use image analysis for context
        if img_result.get('layout_type') == 'simple':
            # Might be video player
            if result['content_type'] == 'unknown':
                result['content_type'] = 'video'
    
    def _merge_clip_result(self, result: Dict, clip_result: Dict):
        """Merge CLIP classification results."""
        if clip_result.get('confidence', 0) > result.get('confidence', 0):
            classification = clip_result.get('classification', '')
            
            if classification:
                result['content_category'] = classification
                result['confidence'] = clip_result['confidence']
                result['detection_method'] = 'clip'
                
                # Map classification to activity type
                activity_map = {
                    'tutorial': 'educational',
                    'coding': 'productive',
                    'documentary': 'educational',
                    'gaming': 'gaming',
                    'anime': 'entertainment',
                    'cartoon': 'entertainment',
                    'music_video': 'entertainment',
                    'movie_series': 'entertainment',
                    'comedy': 'entertainment',
                    'vlog': 'entertainment',
                    'live_stream': 'entertainment',
                    'social_feed': 'social_media',
                    'news': 'news',
                    'sports': 'entertainment',
                    'adult': 'adult',
                }
                
                result['activity_type'] = activity_map.get(classification, result['activity_type'])
    
    def _apply_rules(self, result: Dict, app_name: str, window_title: str, is_browser: bool):
        """Apply rule-based classification."""
        app_lower = app_name.lower() if app_name else ''
        title_lower = window_title.lower() if window_title else ''
        
        # Code editors
        if any(ed in app_lower for ed in ['code', 'sublime', 'atom', 'vim', 'emacs', 'idea', 'pycharm']):
            result['content_type'] = 'code'
            result['activity_type'] = 'productive'
            result['confidence'] = max(result['confidence'], 0.9)
        
        # Terminal
        elif any(term in app_lower for term in ['terminal', 'konsole', 'xterm', 'alacritty', 'kitty']):
            result['content_type'] = 'terminal'
            result['activity_type'] = 'productive'
            result['confidence'] = max(result['confidence'], 0.85)
        
        # Video players
        elif any(player in app_lower for player in ['vlc', 'mpv', 'totem', 'celluloid']):
            result['content_type'] = 'video'
            result['activity_type'] = 'entertainment'
            result['confidence'] = max(result['confidence'], 0.8)
        
        # Browser with known sites
        elif is_browser:
            if 'youtube' in title_lower:
                result['content_type'] = 'video'
                result['content_category'] = 'youtube'
                if any(word in title_lower for word in ['tutorial', 'learn', 'course', 'how to']):
                    result['activity_type'] = 'educational'
                else:
                    result['activity_type'] = 'entertainment'
            elif 'github' in title_lower:
                result['content_type'] = 'code'
                result['activity_type'] = 'productive'
            elif any(social in title_lower for social in ['facebook', 'twitter', 'instagram', 'reddit']):
                result['content_type'] = 'social_feed'
                result['activity_type'] = 'social_media'
    
    def _calculate_productivity(self, activity_type: str) -> float:
        """Calculate productivity score for activity type."""
        scores = {
            'productive': 1.0,
            'educational': 0.8,
            'neutral': 0.0,
            'news': -0.1,
            'shopping': -0.2,
            'entertainment': -0.3,
            'social_media': -0.4,
            'gaming': -0.3,
            'adult': -1.0,
        }
        return scores.get(activity_type, 0.0)
    
    def _generate_description(self, result: Dict, app_name: str, window_title: str) -> str:
        """Generate human-readable description."""
        activity_type = result.get('activity_type', 'unknown')
        content_category = result.get('content_category', '')
        
        if activity_type == 'productive':
            if 'code' in content_category:
                return f"Coding in {app_name}"
            return f"Working in {app_name}"
        
        elif activity_type == 'educational':
            return f"Learning: {content_category.replace('_', ' ').title()}"
        
        elif activity_type == 'entertainment':
            if content_category:
                return f"Watching: {content_category.replace('_', ' ').title()}"
            return f"Entertainment in {app_name}"
        
        elif activity_type == 'social_media':
            return f"Browsing social media"
        
        elif activity_type == 'gaming':
            return f"Playing game"
        
        else:
            return f"Using {app_name}" if app_name else "Unknown activity"
