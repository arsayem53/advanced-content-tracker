"""
Advanced Content Tracker - Helper Functions
Common utility functions used throughout the application.
"""

import os
import re
import hashlib
import time
import subprocess
import platform
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Callable
from urllib.parse import urlparse, parse_qs
from functools import wraps
from pathlib import Path
import logging
import json


logger = logging.getLogger(__name__)


# ==================== URL Utilities ====================

def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: Full URL string
    
    Returns:
        Domain name (e.g., 'youtube.com')
    """
    if not url:
        return ''
    
    try:
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove port number
        if ':' in domain:
            domain = domain.split(':')[0]
        
        return domain.lower()
    except Exception:
        return ''


def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL.
    
    Args:
        url: YouTube URL
    
    Returns:
        Video ID or None
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_url_path(url: str) -> str:
    """
    Get the path component of a URL.
    
    Args:
        url: Full URL
    
    Returns:
        URL path
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return urlparse(url).path
    except Exception:
        return ''


def hash_url(url: str) -> str:
    """
    Create a hash of a URL for anonymization.
    
    Args:
        url: URL to hash
    
    Returns:
        SHA256 hash of URL
    """
    return hashlib.sha256(url.encode()).hexdigest()[:16]


# ==================== Text Utilities ====================

def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text
    
    Returns:
        Cleaned text
    """
    if not text:
        return ''
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    return text.strip()


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: Input text
        min_length: Minimum keyword length
    
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Convert to lowercase and split
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by length and remove common words
    stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out'}
    keywords = [w for w in words if len(w) >= min_length and w not in stopwords]
    
    return list(set(keywords))


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
    
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text or ''
    
    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string for use as filename.
    
    Args:
        filename: Input filename
    
    Returns:
        Safe filename
    """
    # Remove or replace invalid characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe = re.sub(r'\s+', '_', safe)
    safe = re.sub(r'_+', '_', safe)
    return safe.strip('_')[:255]


def contains_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """
    Check if text contains any of the keywords.
    
    Args:
        text: Text to search
        keywords: List of keywords
        case_sensitive: Case sensitive search
    
    Returns:
        True if any keyword found
    """
    if not text or not keywords:
        return False
    
    if not case_sensitive:
        text = text.lower()
        keywords = [k.lower() for k in keywords]
    
    return any(kw in text for kw in keywords)


# ==================== Time Utilities ====================

def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., '2h 30m')
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"


def format_time_ago(dt: datetime) -> str:
    """
    Format datetime as time ago string.
    
    Args:
        dt: Datetime object
    
    Returns:
        Formatted string (e.g., '5 minutes ago')
    """
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def get_date_range(period: str) -> Tuple[datetime, datetime]:
    """
    Get start and end datetime for a period.
    
    Args:
        period: Period name ('today', 'yesterday', 'week', 'month')
    
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if period == 'today':
        return today_start, now
    elif period == 'yesterday':
        yesterday = today_start - timedelta(days=1)
        return yesterday, today_start
    elif period == 'week':
        week_start = today_start - timedelta(days=today_start.weekday())
        return week_start, now
    elif period == 'month':
        month_start = today_start.replace(day=1)
        return month_start, now
    else:
        return today_start, now


def is_within_hours(start_time: str, end_time: str) -> bool:
    """
    Check if current time is within specified hours.
    
    Args:
        start_time: Start time (HH:MM)
        end_time: End time (HH:MM)
    
    Returns:
        True if current time is within range
    """
    now = datetime.now().time()
    start = datetime.strptime(start_time, '%H:%M').time()
    end = datetime.strptime(end_time, '%H:%M').time()
    
    if start <= end:
        return start <= now <= end
    else:
        # Handle overnight ranges (e.g., 22:00 to 08:00)
        return now >= start or now <= end


# ==================== System Utilities ====================

def get_system_info() -> Dict[str, str]:
    """
    Get system information.
    
    Returns:
        Dictionary with system info
    """
    return {
        'os': platform.system(),
        'os_release': platform.release(),
        'os_version': platform.version(),
        'machine': platform.machine(),
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }


def is_wayland() -> bool:
    """
    Check if running on Wayland.
    
    Returns:
        True if Wayland session
    """
    return os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'


def is_x11() -> bool:
    """
    Check if running on X11.
    
    Returns:
        True if X11 session
    """
    return os.environ.get('XDG_SESSION_TYPE', '').lower() == 'x11' or \
           os.environ.get('DISPLAY', '') != ''


def run_command(command: List[str], timeout: int = 10) -> Tuple[str, str, int]:
    """
    Run a shell command.
    
    Args:
        command: Command and arguments
        timeout: Timeout in seconds
    
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return '', 'Command timed out', -1
    except Exception as e:
        return '', str(e), -1


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists on the system.
    
    Args:
        command: Command name
    
    Returns:
        True if command exists
    """
    try:
        subprocess.run(
            ['which', command],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_memory_usage() -> Dict[str, int]:
    """
    Get current process memory usage.
    
    Returns:
        Dictionary with memory info in MB
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        return {
            'rss': mem.rss // (1024 * 1024),  # Resident Set Size
            'vms': mem.vms // (1024 * 1024),  # Virtual Memory Size
        }
    except Exception:
        return {'rss': 0, 'vms': 0}


# ==================== File Utilities ====================

def ensure_dir(path: str) -> str:
    """
    Ensure directory exists, create if not.
    
    Args:
        path: Directory path
    
    Returns:
        Absolute path
    """
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def get_file_size(path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        path: File path
    
    Returns:
        File size in bytes, 0 if not exists
    """
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ==================== Decorators ====================

def timing(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        logger.debug(f"{func.__name__} took {duration:.2f}ms")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def singleton(cls):
    """
    Decorator to make a class a singleton.
    """
    instances = {}
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def cached(ttl_seconds: int = 300):
    """
    Decorator to cache function results.
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result
            
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    
    return decorator


# ==================== Data Utilities ====================

def safe_json_loads(data: str, default: Any = None) -> Any:
    """
    Safely parse JSON string.
    
    Args:
        data: JSON string
        default: Default value on failure
    
    Returns:
        Parsed data or default
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = '{}') -> str:
    """
    Safely serialize to JSON string.
    
    Args:
        data: Data to serialize
        default: Default value on failure
    
    Returns:
        JSON string or default
    """
    try:
        return json.dumps(data)
    except (TypeError, ValueError):
        return default


def merge_dicts(base: Dict, override: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage safely.
    
    Args:
        part: Part value
        total: Total value
    
    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return min(100.0, max(0.0, (part / total) * 100))


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))
