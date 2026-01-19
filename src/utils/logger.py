"""
Advanced Content Tracker - Logging Setup
Configures logging with colored output and file rotation.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional
from pathlib import Path

# Try to import colorlog for colored console output
try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

# Try to import rich for enhanced output
try:
    from rich.logging import RichHandler
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# Log format strings
SIMPLE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DETAILED_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
COLOR_FORMAT = '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s'
RICH_FORMAT = '%(message)s'

# Color scheme for colorlog
COLOR_SCHEME = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}


class LoggerManager:
    """
    Manages logging configuration for the application.
    """
    
    _initialized: bool = False
    _log_dir: str = 'logs'
    _log_file: str = 'app.log'
    _level: int = logging.INFO
    _use_color: bool = True
    _use_rich: bool = False
    
    @classmethod
    def setup(
        cls,
        level: str = 'INFO',
        log_dir: str = 'logs',
        log_file: str = 'app.log',
        use_color: bool = True,
        use_rich: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        log_to_console: bool = True,
        log_to_file: bool = True
    ):
        """
        Set up logging configuration.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            log_file: Log file name
            use_color: Use colored console output
            use_rich: Use rich library for console output
            max_file_size: Max size of log file before rotation
            backup_count: Number of backup files to keep
            log_to_console: Enable console logging
            log_to_file: Enable file logging
        """
        if cls._initialized:
            return
        
        cls._log_dir = log_dir
        cls._log_file = log_file
        cls._level = getattr(logging, level.upper(), logging.INFO)
        cls._use_color = use_color and HAS_COLORLOG
        cls._use_rich = use_rich and HAS_RICH
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(cls._level)
        
        # Remove existing handlers
        root_logger.handlers = []
        
        # Add console handler
        if log_to_console:
            console_handler = cls._create_console_handler()
            root_logger.addHandler(console_handler)
        
        # Add file handler
        if log_to_file:
            file_handler = cls._create_file_handler(max_file_size, backup_count)
            root_logger.addHandler(file_handler)
        
        # Set levels for noisy libraries
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('transformers').setLevel(logging.WARNING)
        logging.getLogger('torch').setLevel(logging.WARNING)
        
        cls._initialized = True
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized - Level: {level}, Dir: {log_dir}")
    
    @classmethod
    def _create_console_handler(cls) -> logging.Handler:
        """Create console log handler with optional colors."""
        if cls._use_rich:
            handler = RichHandler(
                level=cls._level,
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True
            )
            handler.setFormatter(logging.Formatter(RICH_FORMAT))
        elif cls._use_color:
            handler = colorlog.StreamHandler()
            handler.setFormatter(colorlog.ColoredFormatter(
                COLOR_FORMAT,
                log_colors=COLOR_SCHEME,
                secondary_log_colors={},
                style='%'
            ))
        else:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(SIMPLE_FORMAT))
        
        handler.setLevel(cls._level)
        return handler
    
    @classmethod
    def _create_file_handler(
        cls,
        max_size: int,
        backup_count: int
    ) -> logging.Handler:
        """Create rotating file handler."""
        log_path = os.path.join(cls._log_dir, cls._log_file)
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter(DETAILED_FORMAT))
        handler.setLevel(cls._level)
        
        return handler
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (usually __name__)
        
        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.setup()
        return logging.getLogger(name)
    
    @classmethod
    def set_level(cls, level: str):
        """
        Change log level at runtime.
        
        Args:
            level: New log level
        """
        new_level = getattr(logging, level.upper(), logging.INFO)
        cls._level = new_level
        
        root_logger = logging.getLogger()
        root_logger.setLevel(new_level)
        
        for handler in root_logger.handlers:
            handler.setLevel(new_level)
    
    @classmethod
    def add_file_handler(cls, filename: str, level: str = None):
        """
        Add an additional file handler.
        
        Args:
            filename: Log file name
            level: Log level for this handler
        """
        log_path = os.path.join(cls._log_dir, filename)
        handler_level = getattr(logging, level.upper(), cls._level) if level else cls._level
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter(DETAILED_FORMAT))
        handler.setLevel(handler_level)
        
        logging.getLogger().addHandler(handler)
    
    @classmethod
    def create_activity_logger(cls) -> logging.Logger:
        """
        Create a separate logger for activity tracking.
        Logs to a dedicated file with less verbose format.
        """
        logger = logging.getLogger('activity_tracker')
        logger.setLevel(logging.INFO)
        
        # Don't propagate to root logger
        logger.propagate = False
        
        # Activity log file
        log_path = os.path.join(cls._log_dir, 'activity.log')
        
        handler = TimedRotatingFileHandler(
            log_path,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        logger.addHandler(handler)
        
        return logger


def setup_logging(
    level: str = 'INFO',
    log_dir: str = 'logs',
    use_color: bool = True
):
    """
    Convenience function to set up logging.
    
    Args:
        level: Log level
        log_dir: Directory for log files
        use_color: Use colored output
    """
    LoggerManager.setup(
        level=level,
        log_dir=log_dir,
        use_color=use_color
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return LoggerManager.get_logger(name)


# Activity logger for structured tracking logs
class ActivityLogger:
    """
    Specialized logger for activity tracking events.
    Provides structured logging for easy parsing.
    """
    
    def __init__(self):
        self._logger = LoggerManager.create_activity_logger()
    
    def log_activity(
        self,
        app: str,
        window: str,
        activity_type: str,
        content_desc: str,
        confidence: float
    ):
        """Log an activity event."""
        self._logger.info(
            f"APP={app} | WINDOW={window[:50]} | "
            f"TYPE={activity_type} | DESC={content_desc} | "
            f"CONF={confidence:.2f}"
        )
    
    def log_detection(
        self,
        method: str,
        result: str,
        confidence: float,
        duration_ms: float
    ):
        """Log a detection result."""
        self._logger.info(
            f"DETECTION | METHOD={method} | RESULT={result} | "
            f"CONF={confidence:.2f} | TIME={duration_ms:.0f}ms"
        )
    
    def log_error(self, error: str, context: str = ''):
        """Log an error event."""
        self._logger.error(f"ERROR | {context} | {error}")
    
    def log_event(self, event_type: str, details: str):
        """Log a general event."""
        self._logger.info(f"EVENT | TYPE={event_type} | {details}")
