"""
Utilities module - Configuration, logging, and helper functions.
"""

from .config import (
    Config,
    get_config,
    load_config,
    MonitoringConfig,
    DetectionConfig,
    PerformanceConfig,
    PrivacyConfig,
    NotificationsConfig
)

from .logger import (
    LoggerManager,
    setup_logging,
    get_logger,
    ActivityLogger
)

from .helpers import (
    # URL utilities
    extract_domain,
    extract_youtube_video_id,
    get_url_path,
    hash_url,
    
    # Text utilities
    clean_text,
    extract_keywords,
    truncate_text,
    sanitize_filename,
    contains_keywords,
    
    # Time utilities
    format_duration,
    format_time_ago,
    get_date_range,
    is_within_hours,
    
    # System utilities
    get_system_info,
    is_wayland,
    is_x11,
    run_command,
    check_command_exists,
    get_memory_usage,
    
    # File utilities
    ensure_dir,
    get_file_size,
    format_size,
    
    # Decorators
    timing,
    retry,
    singleton,
    cached,
    
    # Data utilities
    safe_json_loads,
    safe_json_dumps,
    merge_dicts,
    calculate_percentage,
    clamp
)

__all__ = [
    # Config
    'Config',
    'get_config',
    'load_config',
    'MonitoringConfig',
    'DetectionConfig',
    'PerformanceConfig',
    'PrivacyConfig',
    'NotificationsConfig',
    
    # Logging
    'LoggerManager',
    'setup_logging',
    'get_logger',
    'ActivityLogger',
    
    # URL utilities
    'extract_domain',
    'extract_youtube_video_id',
    'get_url_path',
    'hash_url',
    
    # Text utilities
    'clean_text',
    'extract_keywords',
    'truncate_text',
    'sanitize_filename',
    'contains_keywords',
    
    # Time utilities
    'format_duration',
    'format_time_ago',
    'get_date_range',
    'is_within_hours',
    
    # System utilities
    'get_system_info',
    'is_wayland',
    'is_x11',
    'run_command',
    'check_command_exists',
    'get_memory_usage',
    
    # File utilities
    'ensure_dir',
    'get_file_size',
    'format_size',
    
    # Decorators
    'timing',
    'retry',
    'singleton',
    'cached',
    
    # Data utilities
    'safe_json_loads',
    'safe_json_dumps',
    'merge_dicts',
    'calculate_percentage',
    'clamp'
]
