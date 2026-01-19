"""
CLIP Analyzer - Advanced content classification using CLIP model.
"""

import logging
from typing import Dict, Any, Optional, List
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import CLIP
try:
    import torch
    import open_clip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False
    logger.warning("open_clip not installed. CLIP analysis will be disabled.")


class CLIPAnalyzer:
    """
    Uses CLIP for advanced image+text classification.
    More accurate than rule-based methods for video/content classification.
    """
    
    # Content categories to classify
    CONTENT_CATEGORIES = [
        "a cartoon or animated video",
        "an anime video",
        "a music video",
        "a gaming video or gameplay",
        "a tutorial or educational video",
        "a movie or TV series",
        "a documentary",
        "a comedy or funny video",
        "a news broadcast",
        "a sports video",
        "a vlog or personal video",
        "a live stream",
        "a coding or programming screen",
        "a social media feed",
        "a website or article",
        "a video player interface",
        "a desktop or file manager",
        "an adult or inappropriate content",
    ]
    
    def __init__(self, model_name: str = "ViT-B-32", device: str = None):
        """
        Initialize CLIP Analyzer.
        
        Args:
            model_name: CLIP model variant
            device: Device to use (cpu/cuda)
        """
        self.logger = logging.getLogger("CLIPAnalyzer")
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.device = device
        self.model_name = model_name
        self._initialized = False
        
        if not HAS_CLIP:
            self.logger.warning("CLIP not available")
    
    def _initialize(self):
        """Lazy initialization of CLIP model."""
        if self._initialized or not HAS_CLIP:
            return False
        
        try:
            self.logger.info(f"Loading CLIP model: {self.model_name}")
            
            # Determine device
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load model
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                self.model_name,
                pretrained='openai'
            )
            self.tokenizer = open_clip.get_tokenizer(self.model_name)
            
            self.model = self.model.to(self.device)
            self.model.eval()
            
            self._initialized = True
            self.logger.info(f"CLIP model loaded on {self.device}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CLIP: {e}")
            self._initialized = False
            return False
    
    def classify(self, image: Image.Image, categories: List[str] = None) -> Dict[str, Any]:
        """
        Classify image content using CLIP.
        
        Args:
            image: PIL Image
            categories: Custom categories (uses default if None)
            
        Returns:
            Classification results
        """
        if not HAS_CLIP:
            return self._fallback_classification(image)
        
        if not self._initialized:
            if not self._initialize():
                return self._fallback_classification(image)
        
        if image is None:
            return {}
        
        if categories is None:
            categories = self.CONTENT_CATEGORIES
        
        try:
            # Preprocess image
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Tokenize text
            text_inputs = self.tokenizer(categories).to(self.device)
            
            # Get features
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_inputs)
                
                # Normalize features
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
                # Calculate similarity
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                
                # Get top predictions
                values, indices = similarity[0].topk(5)
            
            # Build results
            top_category = categories[indices[0].item()]
            top_confidence = values[0].item()
            
            results = {
                'classification': self._parse_category(top_category),
                'confidence': float(top_confidence),
                'top_5': [
                    {'category': self._parse_category(categories[idx.item()]), 'score': float(val.item())}
                    for val, idx in zip(values, indices)
                ],
                'is_nsfw': 'adult' in top_category.lower() or 'inappropriate' in top_category.lower(),
                'detection_method': 'clip',
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"CLIP classification failed: {e}")
            return self._fallback_classification(image)
    
    def _parse_category(self, category: str) -> str:
        """Parse category string to simple label."""
        # Remove common prefixes
        category = category.replace("a ", "").replace("an ", "")
        
        # Map to simple labels
        mappings = {
            "cartoon or animated video": "cartoon",
            "anime video": "anime",
            "music video": "music_video",
            "gaming video or gameplay": "gaming",
            "tutorial or educational video": "tutorial",
            "movie or TV series": "movie_series",
            "documentary": "documentary",
            "comedy or funny video": "comedy",
            "news broadcast": "news",
            "sports video": "sports",
            "vlog or personal video": "vlog",
            "live stream": "live_stream",
            "coding or programming screen": "coding",
            "social media feed": "social_feed",
            "website or article": "article",
            "video player interface": "video_player",
            "desktop or file manager": "desktop",
            "adult or inappropriate content": "adult",
        }
        
        for key, value in mappings.items():
            if key in category:
                return value
        
        return category.replace(" ", "_").lower()
    
    def _fallback_classification(self, image: Image.Image) -> Dict[str, Any]:
        """Fallback classification when CLIP is not available."""
        return {
            'classification': 'unknown',
            'confidence': 0.0,
            'detection_method': 'fallback',
            'is_nsfw': False,
        }
