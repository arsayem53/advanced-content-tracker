"""
Advanced Content Tracker - Screenshot Capture
Handles screenshot capture for both X11 and Wayland environments.
"""

import os
import time
import subprocess
import tempfile
import logging
from typing import Optional, Tuple, List
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

# Try to import mss for cross-platform screenshots
try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

logger = logging.getLogger(__name__)


def check_command_exists(command: str) -> bool:
    """Check if a command exists on the system."""
    try:
        subprocess.run(
            ['which', command],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_command(command: List[str], timeout: int = 10) -> Tuple[str, str, int]:
    """Run a shell command."""
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


def ensure_dir(path: str) -> str:
    """Ensure directory exists."""
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


class ScreenshotCapture:
    """
    Handles screenshot capture with support for X11 and Wayland.
    Automatically detects the display server and uses appropriate method.
    """
    
    def __init__(self):
        """Initialize screenshot capture."""
        self._mss = None
        self._screenshot_dir = None
        
        # Detect display server
        self._display_server = self._detect_display_server()
        
        # Select capture method
        self._capture_method = self._select_capture_method()
        
        logger.info(f"Screenshot capture initialized: {self._display_server} using {self._capture_method}")
    
    def _detect_display_server(self) -> str:
        """Detect which display server is running."""
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        
        if session_type == 'wayland':
            return 'wayland'
        elif session_type == 'x11':
            return 'x11'
        elif os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        elif os.environ.get('DISPLAY'):
            return 'x11'
        else:
            logger.warning("Could not detect display server, defaulting to X11")
            return 'x11'
    
    def _select_capture_method(self) -> str:
        """Select the best available capture method."""
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if self._display_server == 'wayland':
            # GNOME-based desktops (GNOME, Ubuntu, Zorin, Pop!_OS)
            if any(de in desktop for de in ['gnome', 'zorin', 'ubuntu', 'pop', 'unity']):
                if check_command_exists('gnome-screenshot'):
                    logger.info("Using gnome-screenshot for GNOME Wayland")
                    return 'gnome-screenshot'
            
            # KDE Plasma Wayland
            if 'kde' in desktop or 'plasma' in desktop:
                if check_command_exists('spectacle'):
                    logger.info("Using spectacle for KDE Wayland")
                    return 'spectacle'
            
            # Wlroots-based compositors (Sway, Hyprland, etc.)
            if check_command_exists('grim'):
                logger.info("Using grim for wlroots Wayland")
                return 'grim'
            
            # Fallbacks
            if check_command_exists('gnome-screenshot'):
                return 'gnome-screenshot'
            if check_command_exists('spectacle'):
                return 'spectacle'
            if check_command_exists('flameshot'):
                return 'flameshot'
            
            logger.warning("No suitable Wayland screenshot tool found!")
            return 'none'
        
        else:  # X11
            if HAS_MSS:
                logger.info("Using mss for X11")
                return 'mss'
            if check_command_exists('scrot'):
                return 'scrot'
            if check_command_exists('gnome-screenshot'):
                return 'gnome-screenshot'
            if check_command_exists('import'):
                return 'import'
            
            logger.warning("No suitable X11 screenshot tool found!")
            return 'none'
    
    def capture(self, monitor: int = 0) -> Optional[Image.Image]:
        """
        Capture a screenshot.
        
        Args:
            monitor: Monitor index (0 = primary/all, 1+ = specific monitor)
        
        Returns:
            PIL Image or None if capture failed
        """
        try:
            if self._capture_method == 'mss':
                return self._capture_mss(monitor)
            elif self._capture_method == 'grim':
                return self._capture_grim(monitor)
            elif self._capture_method == 'gnome-screenshot':
                return self._capture_gnome_screenshot()
            elif self._capture_method == 'spectacle':
                return self._capture_spectacle()
            elif self._capture_method == 'flameshot':
                return self._capture_flameshot()
            elif self._capture_method == 'scrot':
                return self._capture_scrot()
            elif self._capture_method == 'import':
                return self._capture_import()
            else:
                logger.error("No screenshot capture method available")
                return None
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None
    
    def _capture_mss(self, monitor: int = 0) -> Optional[Image.Image]:
        """Capture using mss library (X11)."""
        try:
            if self._mss is None:
                self._mss = mss.mss()
            
            # Get monitors (index 0 is all monitors combined)
            monitors = self._mss.monitors
            
            if monitor >= len(monitors):
                monitor = 0
            
            # Capture screenshot
            sct_img = self._mss.grab(monitors[monitor])
            
            # Convert to PIL Image
            img = Image.frombytes(
                'RGB',
                (sct_img.width, sct_img.height),
                sct_img.rgb
            )
            
            return img
        except Exception as e:
            logger.error(f"MSS capture failed: {e}")
            # Try to reinitialize mss
            self._mss = None
            return None
    
    def _capture_grim(self, monitor: int = 0) -> Optional[Image.Image]:
        """Capture using grim (Wayland/Sway)."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Build command
            cmd = ['grim', tmp_path]
            
            # Run grim
            stdout, stderr, code = run_command(cmd, timeout=10)
            
            if code == 0 and os.path.exists(tmp_path):
                img = Image.open(tmp_path)
                img.load()  # Force load before deleting file
                os.unlink(tmp_path)
                return img
            else:
                logger.error(f"grim failed: {stderr}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None
        except Exception as e:
            logger.error(f"grim capture failed: {e}")
            return None
    
    def _capture_gnome_screenshot(self) -> Optional[Image.Image]:
        """Capture using gnome-screenshot."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Remove the temp file first (gnome-screenshot needs to create it)
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
            cmd = ['gnome-screenshot', '-f', tmp_path]
            stdout, stderr, code = run_command(cmd, timeout=15)
            
            # Give it a moment to save the file
            time.sleep(0.1)
            
            if os.path.exists(tmp_path):
                img = Image.open(tmp_path)
                img.load()
                os.unlink(tmp_path)
                return img
            else:
                logger.error(f"gnome-screenshot failed: file not created. stderr: {stderr}")
                return None
        except Exception as e:
            logger.error(f"gnome-screenshot capture failed: {e}")
            return None
    
    def _capture_spectacle(self) -> Optional[Image.Image]:
        """Capture using spectacle (KDE)."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            cmd = ['spectacle', '-b', '-n', '-o', tmp_path]
            stdout, stderr, code = run_command(cmd, timeout=15)
            
            time.sleep(0.1)
            
            if os.path.exists(tmp_path):
                img = Image.open(tmp_path)
                img.load()
                os.unlink(tmp_path)
                return img
            else:
                logger.error(f"spectacle failed: {stderr}")
                return None
        except Exception as e:
            logger.error(f"spectacle capture failed: {e}")
            return None
    
    def _capture_flameshot(self) -> Optional[Image.Image]:
        """Capture using flameshot."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            cmd = ['flameshot', 'full', '-p', os.path.dirname(tmp_path)]
            stdout, stderr, code = run_command(cmd, timeout=15)
            
            time.sleep(0.1)
            
            if os.path.exists(tmp_path):
                img = Image.open(tmp_path)
                img.load()
                os.unlink(tmp_path)
                return img
            else:
                logger.error(f"flameshot failed: {stderr}")
                return None
        except Exception as e:
            logger.error(f"flameshot capture failed: {e}")
            return None
    
    def _capture_scrot(self) -> Optional[Image.Image]:
        """Capture using scrot (X11)."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            cmd = ['scrot', '-o', tmp_path]
            stdout, stderr, code = run_command(cmd, timeout=10)
            
            if code == 0 and os.path.exists(tmp_path):
                img = Image.open(tmp_path)
                img.load()
                os.unlink(tmp_path)
                return img
            else:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None
        except Exception as e:
            logger.error(f"scrot capture failed: {e}")
            return None
    
    def _capture_import(self) -> Optional[Image.Image]:
        """Capture using ImageMagick import command (X11)."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            cmd = ['import', '-window', 'root', tmp_path]
            stdout, stderr, code = run_command(cmd, timeout=10)
            
            if code == 0 and os.path.exists(tmp_path):
                img = Image.open(tmp_path)
                img.load()
                os.unlink(tmp_path)
                return img
            else:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None
        except Exception as e:
            logger.error(f"ImageMagick import capture failed: {e}")
            return None
    
    def capture_and_resize(
        self,
        max_size: Tuple[int, int] = (1920, 1080),
        monitor: int = 0
    ) -> Optional[Image.Image]:
        """
        Capture screenshot and resize if larger than max_size.
        
        Args:
            max_size: Maximum dimensions (width, height)
            monitor: Monitor index
        
        Returns:
            PIL Image or None
        """
        img = self.capture(monitor)
        if img is None:
            return None
        
        # Resize if needed
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        return img
    
    def save_screenshot(self, img: Image.Image, prefix: str = 'screenshot') -> Optional[str]:
        """
        Save screenshot to disk.
        
        Args:
            img: PIL Image to save
            prefix: Filename prefix
        
        Returns:
            Path to saved file or None
        """
        if self._screenshot_dir is None:
            self._screenshot_dir = ensure_dir('data/screenshots')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(self._screenshot_dir, filename)
        
        try:
            img.save(filepath, 'PNG', optimize=True)
            logger.debug(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return None
    
    def cleanup_old_screenshots(self, max_count: int = 1000):
        """
        Remove old screenshots if over limit.
        
        Args:
            max_count: Maximum screenshots to keep
        """
        if self._screenshot_dir is None or not os.path.exists(self._screenshot_dir):
            return
        
        try:
            # Get all screenshots sorted by modification time
            files = []
            for f in os.listdir(self._screenshot_dir):
                if f.endswith('.png'):
                    path = os.path.join(self._screenshot_dir, f)
                    files.append((path, os.path.getmtime(path)))
            
            files.sort(key=lambda x: x[1])
            
            # Remove oldest files if over limit
            while len(files) > max_count:
                old_file = files.pop(0)[0]
                os.unlink(old_file)
                logger.debug(f"Removed old screenshot: {old_file}")
        except Exception as e:
            logger.error(f"Failed to cleanup screenshots: {e}")
    
    def get_screenshot_bytes(self, img: Image.Image, format: str = 'PNG') -> bytes:
        """
        Convert image to bytes.
        
        Args:
            img: PIL Image
            format: Image format
        
        Returns:
            Image bytes
        """
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()
    
    def close(self):
        """Clean up resources."""
        if self._mss:
            try:
                self._mss.close()
            except Exception:
                pass
            self._mss = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Singleton instance
_screenshot_capture: Optional[ScreenshotCapture] = None


def get_screenshot_capture() -> ScreenshotCapture:
    """Get or create screenshot capture singleton."""
    global _screenshot_capture
    if _screenshot_capture is None:
        _screenshot_capture = ScreenshotCapture()
    return _screenshot_capture


def capture_screenshot(monitor: int = 0) -> Optional[Image.Image]:
    """
    Convenience function to capture a screenshot.
    
    Args:
        monitor: Monitor index
    
    Returns:
        PIL Image or None
    """
    return get_screenshot_capture().capture(monitor)
