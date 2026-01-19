# ================================================
# Advanced Content Tracker - Configuration
# ================================================

# General settings
general:
  app_name: "Advanced Content Tracker"
  version: "1.0.0"
  debug: false
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR

# Monitoring settings
monitoring:
  screenshot_interval: 30    # Capture every 30 seconds
  idle_threshold: 300        # Idle after 5 minutes

detection:
  use_clip: true             # Enable AI classification
  use_nudenet: true          # Enable NSFW detection
  use_ocr: true              # Enable text extraction

notifications:
  enabled: true
  distraction_threshold: 1800  # Alert after 30min entertainment

privacy:
  store_screenshots: false   # Don't save screenshots
  excluded_apps:             # Skip these apps
    - keepassxc
    - bitwarden
  
  # Recheck same window after N seconds (avoid duplicate analysis)
  same_window_recheck: 30
  
  # Consider user idle after N seconds of no activity
  idle_threshold: 300
  
  # Save screenshots to disk (privacy concern - disable by default)
  save_screenshots: false
  
  # Maximum screenshots to keep (if save_screenshots is true)
  max_screenshots: 1000
  
  # Screenshot quality (1-100)
  screenshot_quality: 85
  
  # Monitor specific displays (empty = all)
  monitors: []

# Detection settings
detection:
  # Enable/disable detection methods
  use_clip: true
  use_nudenet: true
  use_ocr: true
  use_url_analysis: true
  use_rules: true
  use_image_analysis: true
  
  # Confidence thresholds (0.0 - 1.0)
  min_confidence: 0.6
  high_confidence: 0.85
  
  # CLIP settings
  clip_model: "ViT-B-32"  # Options: ViT-B-32, ViT-L-14, ViT-H-14
  clip_pretrained: "openai"
  
  # OCR settings
  ocr_language: "eng"  # Tesseract language code
  ocr_timeout: 5  # seconds
  
  # Skip analysis if window hasn't changed
  skip_unchanged: true
  
  # Minimum text length to analyze
  min_text_length: 10

# Performance settings
performance:
  # Use GPU if available
  enable_gpu: false
  
  # Maximum memory for ML models (MB)
  max_memory_mb: 2048
  
  # Keep models loaded in memory
  cache_models: true
  
  # Number of worker threads
  worker_threads: 2
  
  # Batch processing size
  batch_size: 1
  
  # Analysis timeout (seconds)
  analysis_timeout: 30

# Content categories
content_categories:
  productive:
    - "coding"
    - "programming"
    - "reading_documentation"
    - "professional_networking"
    - "learning"
    - "writing"
    - "spreadsheet"
    - "presentation"
    - "email_work"
    - "research"
    - "design_work"
  
  educational:
    - "tutorial"
    - "course"
    - "documentation"
    - "technical_article"
    - "lecture"
    - "how_to"
    - "learning_video"
    - "academic"
  
  entertainment:
    - "watching_movie"
    - "watching_series"
    - "music_video"
    - "gaming_entertainment"
    - "comedy"
    - "vlog"
    - "entertainment_video"
    - "streaming"
  
  social_media:
    - "facebook_feed"
    - "twitter_feed"
    - "instagram_feed"
    - "reddit_browsing"
    - "social_messaging"
    - "linkedin_feed"
  
  gaming:
    - "playing_game"
    - "watching_gaming"
    - "game_streaming"
  
  shopping:
    - "online_shopping"
    - "product_browsing"
    - "price_comparison"
  
  news:
    - "reading_news"
    - "news_video"
    - "current_events"
  
  adult:
    - "nsfw_content"
    - "adult_website"
    - "explicit_content"

# Notifications settings
notifications:
  # Enable desktop notifications
  enabled: true
  
  # Notification types
  distraction_alerts: true
  productivity_updates: true
  daily_summary: true
  nsfw_alerts: true
  
  # Distraction threshold (seconds) - notify after this much entertainment
  distraction_threshold: 1800  # 30 minutes
  
  # Productivity update interval (seconds)
  productivity_update_interval: 3600  # 1 hour
  
  # Daily summary time (24h format)
  daily_summary_time: "21:00"
  
  # Quiet hours (no notifications)
  quiet_hours:
    enabled: false
    start: "22:00"
    end: "08:00"

# Privacy settings
privacy:
  # Don't save screenshots to disk
  store_screenshots: false
  
  # Don't log detailed NSFW information
  store_nsfw_details: false
  
  # Hash URLs before storing (anonymization)
  anonymize_urls: false
  
  # Exclude certain apps from tracking
  excluded_apps:
    - "keepassxc"
    - "bitwarden"
    - "1password"
    - "gnome-keyring"
  
  # Exclude windows with titles containing these keywords
  excluded_title_keywords:
    - "password"
    - "private"
    - "incognito"
    - "secret"
  
  # Auto-delete data older than N days (0 = never)
  data_retention_days: 90

# Database settings
database:
  # Database file path (relative to project root)
  path: "data/activity.db"
  
  # Enable WAL mode for better performance
  wal_mode: true
  
  # Vacuum database periodically
  auto_vacuum: true
  
  # Backup interval (days, 0 = disabled)
  backup_interval: 7

# Reports settings
reports:
  # Default report format
  default_format: "json"  # json, csv, html
  
  # Report output directory
  output_dir: "data/reports"
  
  # Include in reports
  include_screenshots: false
  include_urls: true
  include_window_titles: true

# UI settings (for future GUI)
ui:
  # System tray icon
  show_tray_icon: true
  
  # Start minimized
  start_minimized: true
  
  # Theme
  theme: "system"  # system, light, dark

# Productivity scoring weights
scoring:
  weights:
    productive: 1.0
    educational: 0.8
    neutral: 0.0
    entertainment: -0.3
    social_media: -0.4
    gaming: -0.3
    adult: -1.0
  
  # Daily productivity goal (percentage)
  daily_goal: 60

# Focus mode settings
focus_mode:
  # Enable focus mode
  enabled: false
  
  # Block these categories during focus mode
  blocked_categories:
    - "entertainment"
    - "social_media"
    - "gaming"
    - "adult"
  
  # Focus session duration (minutes)
  default_duration: 25  # Pomodoro style
  
  # Break duration (minutes)
  break_duration: 5
