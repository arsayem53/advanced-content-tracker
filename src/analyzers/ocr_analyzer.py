"""
OCR Analyzer - Extracts and classifies text from screenshots.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Import Tesseract OCR (via pytesseract)
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False
    logger.warning("pytesseract not installed. OCR will be disabled.")


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text)
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    return text.strip()


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text."""
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out'}
    keywords = [w for w in words if len(w) >= min_length and w not in stopwords]
    return list(set(keywords))


class OCRAnalyzer:
    """
    Extracts and analyzes text from screenshots.
    Provides keyword detection, language detection, and content suggestions.
    """
    
    def __init__(self):
        """Initialize OCR Analyzer."""
        self.logger = logging.getLogger("OCRAnalyzer")
        
        if not HAS_PYTESSERACT:
            self.logger.warning("pytesseract not available, OCR disabled")
    
    def extract_text(self, image) -> str:
        """
        Extract text from screenshot using OCR.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        if not HAS_PYTESSERACT:
            return ""
        
        if image is None:
            return ""
        
        # Configure Tesseract
        custom_config = r'--oem 3 --psm 6'
        
        try:
            text = pytesseract.image_to_string(image, config=custom_config)
            text = clean_text(text)
            return text
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze extracted text for content classification.
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            Dict with analysis results
        """
        if not text or len(text) < 3:
            return {}
        
        text = clean_text(text)
        text_lower = text.lower()
        
        analysis: Dict[str, Any] = {
            'full_text': text[:500],  # Limit stored text
            'text_length': len(text),
            'keywords': extract_keywords(text),
            'language': self._detect_language(text),
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
        }
        
        # Detect programming language indicators
        lang_detections = {
            'python': any(k in text_lower for k in ['import ', 'def ', 'class ', 'print(', 'self.', 'elif ', 'python']),
            'javascript': any(k in text_lower for k in ['function ', 'const ', 'let ', 'var ', '=>', 'console.']),
            'java': any(k in text_lower for k in ['public static', 'void main', 'system.out', 'import java']),
            'cpp': any(k in text_lower for k in ['#include', 'std::', 'cout', 'cin', 'template<']),
            'html': any(k in text_lower for k in ['<html', '<div', '<span', '<script', '<!doctype']),
            'css': any(k in text_lower for k in ['font-size:', 'margin:', 'padding:', '@media']),
            'sql': any(k in text_lower for k in ['select ', 'from ', 'where ', 'insert ', 'update ']),
        }
        
        for lang, detected in lang_detections.items():
            if detected:
                analysis['programming_language'] = lang
                break
        
        # Detect content type indicators
        analysis['has_code'] = 'programming_language' in analysis
        analysis['has_url'] = bool(re.search(r'https?://|www\.', text))
        
        # Content suggestions based on keywords
        content_suggestions = []
        
        if analysis['has_code']:
            content_suggestions.append('coding')
        
        if any(word in text_lower for word in ['tutorial', 'learn', 'how to', 'guide', 'course']):
            content_suggestions.append('tutorial')
        
        if any(word in text_lower for word in ['subscribe', 'like', 'comment', 'share', 'views']):
            content_suggestions.append('video')
        
        if any(word in text_lower for word in ['episode', 'season', 'series', 'anime']):
            content_suggestions.append('entertainment')
        
        analysis['content_suggestions'] = content_suggestions
        
        return analysis
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character frequency."""
        if not text:
            return 'unknown'
        
        # Very simple heuristic
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_alpha = sum(1 for c in text if c.isalpha())
        
        if total_alpha == 0:
            return 'unknown'
        
        latin_ratio = latin_chars / total_alpha
        
        if latin_ratio > 0.8:
            return 'english'  # Likely English/Latin script
        else:
            return 'other'
    
    def get_text_summary(self, text: str, max_words: int = 50) -> str:
        """
        Get a short summary of the text content.
        
        Args:
            text: Input text
            max_words: Maximum words to keep
            
        Returns:
            Short summary
        """
        text = clean_text(text)
        if not text:
            return ""
        
        words = text.split()[:max_words]
        summary = ' '.join(words)
        
        if len(text.split()) > max_words:
            summary += "..."
        
        return summary
