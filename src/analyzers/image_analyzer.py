"""
Image Analyzer - Basic visual analysis of screenshots.
"""

import logging
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logger.warning("OpenCV not installed. Image analysis will be limited.")


class ImageAnalyzer:
    """
    Performs basic visual analysis of screenshots.
    Detects patterns, colors, layouts, and UI elements.
    """
    
    def __init__(self):
        """Initialize Image Analyzer."""
        self.logger = logging.getLogger("ImageAnalyzer")
    
    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Perform complete image analysis.
        
        Args:
            image: PIL Image
            
        Returns:
            Dict with analysis results
        """
        if image is None:
            return {}
        
        results = {
            'width': image.width,
            'height': image.height,
            'aspect_ratio': image.width / image.height if image.height > 0 else 0,
            'mode': image.mode,
        }
        
        # Add color analysis
        color_info = self.analyze_colors(image)
        results.update(color_info)
        
        # Add layout analysis if OpenCV available
        if HAS_OPENCV:
            layout_info = self.analyze_layout(image)
            results.update(layout_info)
        
        return results
    
    def analyze_colors(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze color distribution in the image.
        
        Args:
            image: PIL Image
            
        Returns:
            Dict with color analysis
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get image as numpy array
            img_array = np.array(image)
            
            # Calculate mean colors
            mean_r = np.mean(img_array[:, :, 0])
            mean_g = np.mean(img_array[:, :, 1])
            mean_b = np.mean(img_array[:, :, 2])
            
            # Calculate brightness (0-255)
            brightness = (mean_r + mean_g + mean_b) / 3
            
            # Determine if dark or light theme
            is_dark = brightness < 128
            
            return {
                'mean_red': float(mean_r),
                'mean_green': float(mean_g),
                'mean_blue': float(mean_b),
                'brightness': float(brightness),
                'is_dark_theme': is_dark,
            }
        except Exception as e:
            self.logger.error(f"Color analysis failed: {e}")
            return {}
    
    def analyze_layout(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze layout and UI patterns.
        
        Args:
            image: PIL Image
            
        Returns:
            Dict with layout analysis
        """
        if not HAS_OPENCV:
            return {}
        
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            
            # Convert RGB to BGR for OpenCV
            cv_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Count edges to detect UI complexity
            edge_count = np.sum(edges > 0)
            total_pixels = edges.shape[0] * edges.shape[1]
            edge_density = edge_count / total_pixels if total_pixels > 0 else 0
            
            # Determine layout type based on edge density
            if edge_density > 0.15:
                layout_type = 'complex'  # Lots of UI elements
            elif edge_density > 0.05:
                layout_type = 'moderate'  # Some UI elements
            else:
                layout_type = 'simple'  # Minimal UI (video player, etc.)
            
            return {
                'edge_density': float(edge_density),
                'layout_type': layout_type,
                'ui_complexity': 'high' if edge_density > 0.15 else 'medium' if edge_density > 0.05 else 'low',
            }
        except Exception as e:
            self.logger.error(f"Layout analysis failed: {e}")
            return {}
    
    def detect_video_player(self, image: Image.Image) -> bool:
        """
        Detect if the image shows a video player.
        
        Args:
            image: PIL Image
            
        Returns:
            True if video player detected
        """
        if not HAS_OPENCV:
            return False
        
        try:
            # Simple heuristic: video players typically have
            # - Dark areas (video content)
            # - Low edge density in center
            # - Controls at bottom
            
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                # Check center region brightness
                h, w = img_array.shape[:2]
                center = img_array[h//4:3*h//4, w//4:3*w//4]
                center_brightness = np.mean(center)
                
                # Video content often has moderate to low brightness
                return center_brightness < 150
            
            return False
        except Exception as e:
            self.logger.error(f"Video player detection failed: {e}")
            return False
