"""
Advanced Content Tracker - Main Daemon
Background service that captures screenshots and analyzes content.
"""

import os
import sys
import signal
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import logging
from dataclasses import dataclass

from .screenshot import ScreenshotCapture, get_screenshot_capture
from .monitor import WindowMonitor, WindowInfo, get_window_monitor
from ..storage.database import Database, get_database
from ..storage.models import Activity, ActivityType
from ..utils.config import get_config, Config
from ..utils.logger import setup_logging, get_logger
from ..utils.helpers import format_duration

logger = logging.getLogger(__name__)


@dataclass
class DaemonState:
    """Current state of the daemon."""
    is_running: bool = False
    is_paused: bool = False
    last_capture_time: Optional[datetime] = None
    last_analysis_time: Optional[datetime] = None
    last_window: Optional[WindowInfo] = None
    total_captures: int = 0
    total_analyses: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    
    @property
    def uptime(self) -> float:
        """Get daemon uptime in seconds."""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0
    
    @property
    def uptime_formatted(self) -> str:
        """Get formatted uptime."""
        return format_duration(int(self.uptime))


class ContentTrackerDaemon:
    """
    Main daemon class that orchestrates all tracking activities.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the daemon.
        
        Args:
            config_path: Optional path to config file
        """
        # Load configuration
        self.config = get_config()
        if config_path:
            self.config.load(config_path)
        
        # Setup logging
        setup_logging(
            level=self.config.log_level,
            log_dir='logs',
            use_color=True
        )
        
        # Initialize state
        self.state = DaemonState()
        
        # Initialize components
        self.screenshot_capture: Optional[ScreenshotCapture] = None
        self.window_monitor: Optional[WindowMonitor] = None
        self.database: Optional[Database] = None
        
        # Analysis components (will be initialized lazily)
        self._content_classifier = None
        
        # Threading
        self._main_thread: Optional[threading.Thread] = None
        self._analysis_queue: queue.Queue = queue.Queue(maxsize=100)
        self._analysis_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self._on_activity_detected: Optional[Callable[[Activity], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None
        
        # Register signal handlers
        self._setup_signal_handlers()
        
        logger.info("Content Tracker Daemon initialized")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, self._reload_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def _reload_handler(self, signum, frame):
        """Handle reload signal (SIGHUP)."""
        logger.info("Received SIGHUP, reloading configuration...")
        self.config.reload()
    
    def _initialize_components(self):
        """Initialize all daemon components."""
        logger.info("Initializing components...")
        
        # Initialize screenshot capture
        self.screenshot_capture = get_screenshot_capture()
        
        # Initialize window monitor
        self.window_monitor = get_window_monitor()
        
        # Initialize database
        self.database = get_database(self.config.database_path)
        
        # Initialize content classifier (lazy load)
        self._init_content_classifier()
        
        logger.info("All components initialized")
    
    def _init_content_classifier(self):
        """Initialize content classifier (lazy loading for performance)."""
        try:
            # Import here to avoid slow startup
            from ..analyzers.content_classifier import ContentClassifier
            self._content_classifier = ContentClassifier()
            logger.info("Content classifier initialized")
        except Exception as e:
            logger.error(f"Failed to initialize content classifier: {e}")
            self._content_classifier = None
    
    def start(self, blocking: bool = True):
        """
        Start the daemon.
        
        Args:
            blocking: If True, blocks until stopped. If False, runs in background thread.
        """
        if self.state.is_running:
            logger.warning("Daemon is already running")
            return
        
        logger.info("Starting Content Tracker Daemon...")
        
        # Initialize components
        self._initialize_components()
        
        # Update state
        self.state.is_running = True
        self.state.start_time = datetime.now()
        self._stop_event.clear()
        
        # Start analysis thread
        self._analysis_thread = threading.Thread(
            target=self._analysis_worker,
            name="AnalysisWorker",
            daemon=True
        )
        self._analysis_thread.start()
        
        if blocking:
            # Run in main thread
            self._main_loop()
        else:
            # Run in background thread
            self._main_thread = threading.Thread(
                target=self._main_loop,
                name="MainLoop",
                daemon=True
            )
            self._main_thread.start()
        
        logger.info("Daemon started successfully")
    
    def stop(self):
        """Stop the daemon gracefully."""
        if not self.state.is_running:
            return
        
        logger.info("Stopping daemon...")
        
        self.state.is_running = False
        self._stop_event.set()
        
        # Wait for threads to finish
        if self._analysis_thread and self._analysis_thread.is_alive():
            self._analysis_thread.join(timeout=5)
        
        if self._main_thread and self._main_thread.is_alive():
            self._main_thread.join(timeout=5)
        
        # Cleanup components
        self._cleanup()
        
        logger.info(f"Daemon stopped. Uptime: {self.state.uptime_formatted}, "
                   f"Captures: {self.state.total_captures}, "
                   f"Analyses: {self.state.total_analyses}")
    
    def pause(self):
        """Pause tracking temporarily."""
        self.state.is_paused = True
        logger.info("Tracking paused")
    
    def resume(self):
        """Resume tracking after pause."""
        self.state.is_paused = False
        logger.info("Tracking resumed")
    
    def _cleanup(self):
        """Clean up resources."""
        if self.screenshot_capture:
            self.screenshot_capture.close()
        
        if self.window_monitor:
            self.window_monitor.close()
        
        if self.database:
            # Update daily stats before closing
            try:
                self.database.update_daily_stats()
                self.database.update_app_usage()
                self.database.update_website_usage()
            except Exception as e:
                logger.error(f"Failed to update stats: {e}")
            
            self.database.close()
    
    def _main_loop(self):
        """Main tracking loop."""
        interval = self.config.monitoring.screenshot_interval
        
        logger.info(f"Starting main loop with {interval}s interval")
        
        while self.state.is_running and not self._stop_event.is_set():
            try:
                if not self.state.is_paused:
                    self._do_capture_cycle()
                
                # Wait for next interval or stop event
                if self._stop_event.wait(timeout=interval):
                    break
                    
            except Exception as e:
                self.state.errors += 1
                logger.error(f"Error in main loop: {e}", exc_info=True)
                
                if self._on_error:
                    self._on_error(e)
                
                # Brief pause before retry
                time.sleep(1)
    
    def _do_capture_cycle(self):
        """Perform one capture and analysis cycle."""
        start_time = time.time()
        
        # Check if user is idle
        if self.window_monitor.is_user_idle():
            self._record_idle_activity()
            return
        
        # Get active window
        window_info = self.window_monitor.get_active_window()
        
        if window_info is None:
            logger.debug("No active window detected")
            return
        
        # Check if window should be excluded
        if self._should_exclude_window(window_info):
            logger.debug(f"Window excluded: {window_info.app_name}")
            return
        
        # Check if window has changed (for skip_unchanged optimization)
        if self.config.detection.skip_unchanged:
            if not self.window_monitor.has_window_changed(window_info):
                # Same window, just update duration
                self._extend_last_activity()
                return
        
        # Capture screenshot
        screenshot = self.screenshot_capture.capture()
        
        if screenshot is None:
            logger.warning("Failed to capture screenshot")
            return
        
        self.state.total_captures += 1
        self.state.last_capture_time = datetime.now()
        
        # Queue for analysis
        try:
            self._analysis_queue.put_nowait({
                'window_info': window_info,
                'screenshot': screenshot,
                'timestamp': datetime.now()
            })
        except queue.Full:
            logger.warning("Analysis queue full, dropping capture")
        
        # Update last window
        self.window_monitor.update_last_window(window_info)
        self.state.last_window = window_info
        
        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"Capture cycle completed in {elapsed:.1f}ms")
    
    def _analysis_worker(self):
        """Worker thread for content analysis."""
        logger.info("Analysis worker started")
        
        while self.state.is_running and not self._stop_event.is_set():
            try:
                # Get item from queue with timeout
                try:
                    item = self._analysis_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Perform analysis
                activity = self._analyze_content(
                    item['window_info'],
                    item['screenshot'],
                    item['timestamp']
                )
                
                if activity:
                    # Store in database
                    self.database.insert_activity(activity)
                    self.state.total_analyses += 1
                    self.state.last_analysis_time = datetime.now()
                    
                    # Trigger callback
                    if self._on_activity_detected:
                        self._on_activity_detected(activity)
                    
                    logger.debug(f"Activity recorded: {activity.content_description}")
                
                self._analysis_queue.task_done()
                
            except Exception as e:
                self.state.errors += 1
                logger.error(f"Analysis error: {e}", exc_info=True)
        
        logger.info("Analysis worker stopped")
    
    def _analyze_content(
        self,
        window_info: WindowInfo,
        screenshot,
        timestamp: datetime
    ) -> Optional[Activity]:
        """
        Analyze captured content and create Activity record.
        
        Args:
            window_info: Active window information
            screenshot: Captured screenshot (PIL Image)
            timestamp: Capture timestamp
        
        Returns:
            Activity object or None
        """
        activity = Activity(
            timestamp=timestamp,
            app_name=window_info.app_name,
            window_title=window_info.window_title,
            process_name=window_info.process_name,
            process_id=window_info.process_id,
            website=window_info.url if window_info.is_browser else "",
            url=window_info.url if window_info.is_browser else "",
            duration=self.config.monitoring.screenshot_interval
        )
        
        # Use content classifier if available
        if self._content_classifier:
            try:
                classification = self._content_classifier.classify(
                    screenshot=screenshot,
                    window_info=window_info
                )
                
                activity.content_type = classification.get('content_type', 'unknown')
                activity.content_category = classification.get('content_category', '')
                activity.content_description = classification.get('description', '')
                activity.content_title = classification.get('title', '')
                activity.activity_type = classification.get('activity_type', 'unknown')
                activity.is_productive = classification.get('is_productive', False)
                activity.productivity_score = classification.get('productivity_score', 0.0)
                activity.detection_method = classification.get('detection_method', 'rules')
                activity.confidence = classification.get('confidence', 0.0)
                activity.nsfw_score = classification.get('nsfw_score', 0.0)
                activity.is_nsfw = classification.get('is_nsfw', False)
                activity.extracted_text = classification.get('extracted_text', '')[:1000]
                
            except Exception as e:
                logger.error(f"Content classification failed: {e}")
                # Fallback to basic classification
                self._basic_classify(activity, window_info)
        else:
            # No classifier, use basic classification
            self._basic_classify(activity, window_info)
        
        # Save screenshot if enabled
        if self.config.monitoring.save_screenshots:
            screenshot_path = self.screenshot_capture.save_screenshot(screenshot)
            if screenshot_path:
                activity.screenshot_path = screenshot_path
        
        return activity
    
    def _basic_classify(self, activity: Activity, window_info: WindowInfo):
        """Basic classification without ML models."""
        app_lower = window_info.app_name.lower()
        title_lower = window_info.window_title.lower()
        
        # Detect activity type based on app/window
        if window_info.is_browser:
            activity.content_type = 'browser'
            activity.activity_type = 'neutral'
            
            # Check for known sites
            if 'youtube' in title_lower or 'youtube' in window_info.url:
                activity.website = 'youtube.com'
                activity.content_category = 'video'
                activity.activity_type = 'entertainment'
                activity.content_description = f"Watching: {window_info.window_title[:50]}"
            elif 'github' in title_lower or 'github' in window_info.url:
                activity.website = 'github.com'
                activity.content_category = 'code'
                activity.activity_type = 'productive'
                activity.is_productive = True
                activity.productivity_score = 0.8
            elif any(site in title_lower for site in ['facebook', 'twitter', 'instagram', 'reddit']):
                activity.content_category = 'social_feed'
                activity.activity_type = 'social_media'
            else:
                activity.content_description = f"Browsing: {window_info.window_title[:50]}"
                
        elif any(editor in app_lower for editor in ['code', 'sublime', 'atom', 'vim', 'emacs', 'idea', 'pycharm']):
            activity.content_type = 'code'
            activity.activity_type = 'productive'
            activity.is_productive = True
            activity.productivity_score = 1.0
            activity.content_description = f"Coding in {window_info.app_name}"
            
        elif any(term in app_lower for term in ['terminal', 'konsole', 'xterm', 'alacritty', 'kitty']):
            activity.content_type = 'terminal'
            activity.activity_type = 'productive'
            activity.is_productive = True
            activity.productivity_score = 0.8
            activity.content_description = "Using terminal"
            
        elif any(player in app_lower for player in ['vlc', 'mpv', 'totem', 'celluloid']):
            activity.content_type = 'video'
            activity.activity_type = 'entertainment'
            activity.content_description = f"Watching: {window_info.window_title[:50]}"
            
        elif any(office in app_lower for office in ['libreoffice', 'word', 'excel', 'writer', 'calc']):
            activity.content_type = 'document'
            activity.activity_type = 'productive'
            activity.is_productive = True
            activity.productivity_score = 0.9
            activity.content_description = f"Working on document: {window_info.window_title[:50]}"
        
        else:
            activity.content_type = 'unknown'
            activity.activity_type = 'neutral'
            activity.content_description = f"Using {window_info.app_name}"
        
        activity.detection_method = 'rules'
        activity.confidence = 0.5
    
    def _should_exclude_window(self, window_info: WindowInfo) -> bool:
        """Check if window should be excluded from tracking."""
        # Check excluded apps
        if self.config.is_app_excluded(window_info.app_name):
            return True
        
        if self.config.is_app_excluded(window_info.process_name):
            return True
        
        # Check excluded title keywords
        if self.config.is_title_excluded(window_info.window_title):
            return True
        
        return False
    
    def _record_idle_activity(self):
        """Record idle activity."""
        activity = Activity(
            timestamp=datetime.now(),
            app_name="System",
            window_title="Idle",
            activity_type=ActivityType.IDLE.value,
            content_type="idle",
            content_description="User is idle",
            is_idle=True,
            duration=self.config.monitoring.screenshot_interval
        )
        
        self.database.insert_activity(activity)
        logger.debug("Recorded idle activity")
    
    def _extend_last_activity(self):
        """Extend duration of last activity (same window)."""
        # This is a optimization - instead of creating new records,
        # we could update the last record's duration
        # For now, just skip creating a new record
        logger.debug("Same window, skipping capture")
    
    def set_activity_callback(self, callback: Callable[[Activity], None]):
        """Set callback for when activity is detected."""
        self._on_activity_detected = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]):
        """Set callback for errors."""
        self._on_error = callback
    
    def get_status(self) -> Dict[str, Any]:
        """Get daemon status."""
        return {
            'is_running': self.state.is_running,
            'is_paused': self.state.is_paused,
            'uptime': self.state.uptime_formatted,
            'total_captures': self.state.total_captures,
            'total_analyses': self.state.total_analyses,
            'errors': self.state.errors,
            'last_capture': self.state.last_capture_time.isoformat() if self.state.last_capture_time else None,
            'last_window': self.state.last_window.to_dict() if self.state.last_window else None,
            'queue_size': self._analysis_queue.qsize()
        }


# Singleton instance
_daemon: Optional[ContentTrackerDaemon] = None


def get_daemon() -> ContentTrackerDaemon:
    """Get or create daemon singleton."""
    global _daemon
    if _daemon is None:
        _daemon = ContentTrackerDaemon()
    return _daemon


def start_daemon(blocking: bool = True, config_path: str = None):
    """Convenience function to start the daemon."""
    daemon = get_daemon()
    if config_path:
        daemon.config.load(config_path)
    daemon.start(blocking=blocking)
    return daemon


def stop_daemon():
    """Convenience function to stop the daemon."""
    global _daemon
    if _daemon:
        _daemon.stop()
        _daemon = None
