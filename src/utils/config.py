"""
Advanced Content Tracker - Configuration Loader
Handles loading, validating, and accessing configuration from YAML files.
"""

import os
import yaml
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


# Default configuration values
DEFAULT_CONFIG = {
    'general': {
        'app_name': 'Advanced Content Tracker',
        'version': '1.0.0',
        'debug': False,
        'log_level': 'INFO'
    },
    'monitoring': {
        'screenshot_interval': 30,
        'same_window_recheck': 30,
        'idle_threshold': 300,
        'save_screenshots': False,
        'max_screenshots': 1000,
        'screenshot_quality': 85,
        'monitors': []
    },
    'detection': {
        'use_clip': True,
        'use_nudenet': True,
        'use_ocr': True,
        'use_url_analysis': True,
        'use_rules': True,
        'use_image_analysis': True,
        'min_confidence': 0.6,
        'high_confidence': 0.85,
        'clip_model': 'ViT-B-32',
        'clip_pretrained': 'openai',
        'ocr_language': 'eng',
        'ocr_timeout': 5,
        'skip_unchanged': True,
        'min_text_length': 10
    },
    'performance': {
        'enable_gpu': False,
        'max_memory_mb': 2048,
        'cache_models': True,
        'worker_threads': 2,
        'batch_size': 1,
        'analysis_timeout': 30
    },
    'content_categories': {
        'productive': ['coding', 'programming', 'reading_documentation', 'professional_networking', 'learning', 'writing', 'spreadsheet', 'presentation', 'email_work', 'research', 'design_work'],
        'educational': ['tutorial', 'course', 'documentation', 'technical_article', 'lecture', 'how_to', 'learning_video', 'academic'],
        'entertainment': ['watching_movie', 'watching_series', 'music_video', 'gaming_entertainment', 'comedy', 'vlog', 'entertainment_video', 'streaming'],
        'social_media': ['facebook_feed', 'twitter_feed', 'instagram_feed', 'reddit_browsing', 'social_messaging', 'linkedin_feed'],
        'gaming': ['playing_game', 'watching_gaming', 'game_streaming'],
        'shopping': ['online_shopping', 'product_browsing', 'price_comparison'],
        'news': ['reading_news', 'news_video', 'current_events'],
        'adult': ['nsfw_content', 'adult_website', 'explicit_content']
    },
    'notifications': {
        'enabled': True,
        'distraction_alerts': True,
        'productivity_updates': True,
        'daily_summary': True,
        'nsfw_alerts': True,
        'distraction_threshold': 1800,
        'productivity_update_interval': 3600,
        'daily_summary_time': '21:00',
        'quiet_hours': {
            'enabled': False,
            'start': '22:00',
            'end': '08:00'
        }
    },
    'privacy': {
        'store_screenshots': False,
        'store_nsfw_details': False,
        'anonymize_urls': False,
        'excluded_apps': ['keepassxc', 'bitwarden', '1password', 'gnome-keyring'],
        'excluded_title_keywords': ['password', 'private', 'incognito', 'secret'],
        'data_retention_days': 90
    },
    'database': {
        'path': 'data/activity.db',
        'wal_mode': True,
        'auto_vacuum': True,
        'backup_interval': 7
    },
    'reports': {
        'default_format': 'json',
        'output_dir': 'data/reports',
        'include_screenshots': False,
        'include_urls': True,
        'include_window_titles': True
    },
    'ui': {
        'show_tray_icon': True,
        'start_minimized': True,
        'theme': 'system'
    },
    'scoring': {
        'weights': {
            'productive': 1.0,
            'educational': 0.8,
            'neutral': 0.0,
            'entertainment': -0.3,
            'social_media': -0.4,
            'gaming': -0.3,
            'adult': -1.0
        },
        'daily_goal': 60
    },
    'focus_mode': {
        'enabled': False,
        'blocked_categories': ['entertainment', 'social_media', 'gaming', 'adult'],
        'default_duration': 25,
        'break_duration': 5
    }
}


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    screenshot_interval: int = 30
    same_window_recheck: int = 30
    idle_threshold: int = 300
    save_screenshots: bool = False
    max_screenshots: int = 1000
    screenshot_quality: int = 85
    monitors: list = field(default_factory=list)


@dataclass
class DetectionConfig:
    """Detection configuration."""
    use_clip: bool = True
    use_nudenet: bool = True
    use_ocr: bool = True
    use_url_analysis: bool = True
    use_rules: bool = True
    use_image_analysis: bool = True
    min_confidence: float = 0.6
    high_confidence: float = 0.85
    clip_model: str = 'ViT-B-32'
    clip_pretrained: str = 'openai'
    ocr_language: str = 'eng'
    ocr_timeout: int = 5
    skip_unchanged: bool = True
    min_text_length: int = 10


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    enable_gpu: bool = False
    max_memory_mb: int = 2048
    cache_models: bool = True
    worker_threads: int = 2
    batch_size: int = 1
    analysis_timeout: int = 30


@dataclass
class PrivacyConfig:
    """Privacy configuration."""
    store_screenshots: bool = False
    store_nsfw_details: bool = False
    anonymize_urls: bool = False
    excluded_apps: list = field(default_factory=list)
    excluded_title_keywords: list = field(default_factory=list)
    data_retention_days: int = 90


@dataclass
class NotificationsConfig:
    """Notifications configuration."""
    enabled: bool = True
    distraction_alerts: bool = True
    productivity_updates: bool = True
    daily_summary: bool = True
    nsfw_alerts: bool = True
    distraction_threshold: int = 1800
    productivity_update_interval: int = 3600
    daily_summary_time: str = '21:00'
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = '22:00'
    quiet_hours_end: str = '08:00'


class Config:
    """
    Configuration manager with lazy loading and caching.
    """
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    _config_path: str = 'config.yaml'
    _loaded: bool = False
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize config (only loads once due to singleton)."""
        if not self._loaded:
            self.load()
    
    def load(self, config_path: str = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, uses default locations.
        
        Returns:
            Loaded configuration dictionary.
        """
        if config_path:
            self._config_path = config_path
        
        # Start with default config
        self._config = self._deep_copy(DEFAULT_CONFIG)
        
        # Try to find and load config file
        config_paths = [
            self._config_path,
            'config.yaml',
            'config.yml',
            os.path.expanduser('~/.config/content-tracker/config.yaml'),
            '/etc/content-tracker/config.yaml'
        ]
        
        loaded_path = None
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        user_config = yaml.safe_load(f) or {}
                    self._merge_config(self._config, user_config)
                    loaded_path = path
                    break
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")
        
        if loaded_path:
            logger.info(f"Configuration loaded from: {loaded_path}")
        else:
            logger.info("Using default configuration (no config file found)")
        
        self._loaded = True
        return self._config
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy a nested dictionary/list structure."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _merge_config(self, base: Dict, override: Dict):
        """
        Recursively merge override config into base config.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'monitoring.screenshot_interval')
            default: Default value if key not found
        
        Returns:
            Configuration value or default.
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'monitoring.screenshot_interval')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, config_path: str = None):
        """
        Save current configuration to YAML file.
        
        Args:
            config_path: Path to save config. If None, uses loaded path.
        """
        path = config_path or self._config_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        with open(path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to: {path}")
    
    def reload(self):
        """Reload configuration from file."""
        self._loaded = False
        self.load()
    
    # ==================== Typed Config Accessors ====================
    
    @property
    def monitoring(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        cfg = self.get('monitoring', {})
        return MonitoringConfig(
            screenshot_interval=cfg.get('screenshot_interval', 30),
            same_window_recheck=cfg.get('same_window_recheck', 30),
            idle_threshold=cfg.get('idle_threshold', 300),
            save_screenshots=cfg.get('save_screenshots', False),
            max_screenshots=cfg.get('max_screenshots', 1000),
            screenshot_quality=cfg.get('screenshot_quality', 85),
            monitors=cfg.get('monitors', [])
        )
    
    @property
    def detection(self) -> DetectionConfig:
        """Get detection configuration."""
        cfg = self.get('detection', {})
        return DetectionConfig(
            use_clip=cfg.get('use_clip', True),
            use_nudenet=cfg.get('use_nudenet', True),
            use_ocr=cfg.get('use_ocr', True),
            use_url_analysis=cfg.get('use_url_analysis', True),
            use_rules=cfg.get('use_rules', True),
            use_image_analysis=cfg.get('use_image_analysis', True),
            min_confidence=cfg.get('min_confidence', 0.6),
            high_confidence=cfg.get('high_confidence', 0.85),
            clip_model=cfg.get('clip_model', 'ViT-B-32'),
            clip_pretrained=cfg.get('clip_pretrained', 'openai'),
            ocr_language=cfg.get('ocr_language', 'eng'),
            ocr_timeout=cfg.get('ocr_timeout', 5),
            skip_unchanged=cfg.get('skip_unchanged', True),
            min_text_length=cfg.get('min_text_length', 10)
        )
    
    @property
    def performance(self) -> PerformanceConfig:
        """Get performance configuration."""
        cfg = self.get('performance', {})
        return PerformanceConfig(
            enable_gpu=cfg.get('enable_gpu', False),
            max_memory_mb=cfg.get('max_memory_mb', 2048),
            cache_models=cfg.get('cache_models', True),
            worker_threads=cfg.get('worker_threads', 2),
            batch_size=cfg.get('batch_size', 1),
            analysis_timeout=cfg.get('analysis_timeout', 30)
        )
    
    @property
    def privacy(self) -> PrivacyConfig:
        """Get privacy configuration."""
        cfg = self.get('privacy', {})
        return PrivacyConfig(
            store_screenshots=cfg.get('store_screenshots', False),
            store_nsfw_details=cfg.get('store_nsfw_details', False),
            anonymize_urls=cfg.get('anonymize_urls', False),
            excluded_apps=cfg.get('excluded_apps', []),
            excluded_title_keywords=cfg.get('excluded_title_keywords', []),
            data_retention_days=cfg.get('data_retention_days', 90)
        )
    
    @property
    def notifications(self) -> NotificationsConfig:
        """Get notifications configuration."""
        cfg = self.get('notifications', {})
        quiet = cfg.get('quiet_hours', {})
        return NotificationsConfig(
            enabled=cfg.get('enabled', True),
            distraction_alerts=cfg.get('distraction_alerts', True),
            productivity_updates=cfg.get('productivity_updates', True),
            daily_summary=cfg.get('daily_summary', True),
            nsfw_alerts=cfg.get('nsfw_alerts', True),
            distraction_threshold=cfg.get('distraction_threshold', 1800),
            productivity_update_interval=cfg.get('productivity_update_interval', 3600),
            daily_summary_time=cfg.get('daily_summary_time', '21:00'),
            quiet_hours_enabled=quiet.get('enabled', False),
            quiet_hours_start=quiet.get('start', '22:00'),
            quiet_hours_end=quiet.get('end', '08:00')
        )
    
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get('general.debug', False)
    
    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get('general.log_level', 'INFO')
    
    @property
    def database_path(self) -> str:
        """Get database path."""
        return self.get('database.path', 'data/activity.db')
    
    def get_content_categories(self, category: str) -> list:
        """Get list of content types for a category."""
        return self.get(f'content_categories.{category}', [])
    
    def get_scoring_weight(self, activity_type: str) -> float:
        """Get productivity scoring weight for an activity type."""
        return self.get(f'scoring.weights.{activity_type}', 0.0)
    
    def is_app_excluded(self, app_name: str) -> bool:
        """Check if an app is excluded from tracking."""
        excluded = self.privacy.excluded_apps
        return any(exc.lower() in app_name.lower() for exc in excluded)
    
    def is_title_excluded(self, title: str) -> bool:
        """Check if a window title contains excluded keywords."""
        keywords = self.privacy.excluded_title_keywords
        title_lower = title.lower()
        return any(kw.lower() in title_lower for kw in keywords)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return self.get(key) is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Return full configuration as dictionary."""
        return self._deep_copy(self._config)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_config(config_path: str = None) -> Config:
    """Load configuration from specified path."""
    global _config
    _config = Config()
    if config_path:
        _config.load(config_path)
    return _config
