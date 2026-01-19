"""
NSFW Detector - Detects adult content in images.
"""

import logging
from typing import Dict, Any
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

try:
    from nudenet import NudeDetector
    HAS_NUDENET = True
except ImportError:
    HAS_NUDENET = False
    logger.warning("NudeNet not installed. NSFW detection will be disabled.")


class NSFWDetector:
    """
    Detects adult content in images using NudeNet.
    """
    
    def __init__(self):
        """Initialize NSFW Detector."""
        self.logger = logging.getLogger("NSFWDetector")
        self._detector = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of NudeNet model."""
        if self._initialized or not HAS_NUDENET:
            return False
        
        try:
            self.logger.info("Loading NudeNet model...")
            self._detector = NudeDetector()
            self._initialized = True
            self.logger.info("NudeNet model loaded")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize NudeNet: {e}")
            return False
    
    def detect(self, image: Image.Image) -> Dict[str, Any]:
        """
        Detect NSFW content in image.
        
        Args:
            image: PIL Image
            
        Returns:
            Dict with NSFW detection results
        """
        if not HAS_NUDENET:
            return self._fallback_result()
        
        if not self._initialized:
            if not self._initialize():
                return self._fallback_result()
        
        if image is None:
            return self._fallback_result()
        
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # NudeNet expects BGR format
            if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                # RGB to BGR
                img_array = img_array[:, :, ::-1] if img_array.shape[2] == 3 else img_array[:, :, :3][:, :, ::-1]
            
            # Run detection
            results = self._detector.detect(img_array)
            
            # Process results
            is_nsfw = False
            nsfw_score = 0.0
            detected_parts = []
            
            if results:
                # NudeNet returns list of detected regions
                nsfw_labels = [
                    'FEMALE_BREAST_EXPOSED', 'FEMALE_GENITALIA_EXPOSED',
                    'MALE_GENITALIA_EXPOSED', 'BUTTOCKS_EXPOSED',
                    'ANUS_EXPOSED', 'FEMALE_BREAST_COVERED',
                    'BELLY_EXPOSED', 'ARMPITS_EXPOSED'
                ]
                
                for detection in results:
                    label = detection.get('class', '')
                    score = detection.get('score', 0)
                    
                    if label in nsfw_labels and score > 0.5:
                        is_nsfw = True
                        nsfw_score = max(nsfw_score, score)
                        detected_parts.append(label)
            
            return {
                'is_nsfw': is_nsfw,
                'nsfw_score': float(nsfw_score),
                'safe_score': float(1.0 - nsfw_score),
                'detected_parts': detected_parts,
                'detection_method': 'nudenet',
            }
            
        except Exception as e:
            self.logger.error(f"NSFW detection failed: {e}")
            return self._fallback_result()
    
    def _fallback_result(self) -> Dict[str, Any]:
        """Return default result when detection fails."""
        return {
            'is_nsfw': False,
            'nsfw_score': 0.0,
            'safe_score': 1.0,
            'detected_parts': [],
            'detection_method': 'fallback',
        }
    
    def classify(self, image: Image.Image) -> Dict[str, Any]:
        """Alias for detect() for compatibility."""
        return self.detect(image)
