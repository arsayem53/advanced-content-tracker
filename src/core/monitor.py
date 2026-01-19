"""
Advanced Content Tracker - Window/Process Monitor
Monitors active windows on Linux (X11 and Wayland).
"""

import os
import re
import subprocess
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class WindowInfo:
    """Information about the active window."""
    window_id: int = 0
    window_title: str = ""
    app_name: str = ""
    process_name: str = ""
    process_id: int = 0
    wm_class: str = ""
    is_browser: bool = False
    url: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'window_id': self.window_id,
            'window_title': self.window_title,
            'app_name': self.app_name,
            'process_name': self.process_name,
            'process_id': self.process_id,
            'wm_class': self.wm_class,
            'is_browser': self.is_browser,
            'url': self.url,
        }


def run_command(cmd, timeout=5):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1


class WindowMonitor:
    """
    Monitors active windows.
    Supports X11 and Wayland (GNOME, KDE, Sway, Hyprland).
    """
    
    BROWSER_NAMES = ['firefox', 'chrome', 'chromium', 'brave', 'opera', 'edge', 'vivaldi', 'librewolf']
    
    def __init__(self):
        self._display_server = self._detect_display_server()
        self._desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        self._last_window = None
        
        logger.info(f"Window monitor initialized: {self._display_server}")
    
    def _detect_display_server(self) -> str:
        """Detect display server type."""
        session = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session == 'wayland':
            return 'wayland'
        elif session == 'x11':
            return 'x11'
        elif os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        elif os.environ.get('DISPLAY'):
            return 'x11'
        return 'unknown'
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get information about the currently active window."""
        try:
            if self._display_server == 'wayland':
                return self._get_window_wayland()
            else:
                return self._get_window_x11()
        except Exception as e:
            logger.error(f"Window detection failed: {e}")
            return None
    
    def _get_window_wayland(self) -> Optional[WindowInfo]:
        """Get active window on Wayland."""
        
        # Try GNOME first
        if 'gnome' in self._desktop or 'zorin' in self._desktop or 'ubuntu' in self._desktop:
            result = self._get_window_gnome()
            if result and result.app_name:
                return result
        
        # Try Sway
        result = self._get_window_sway()
        if result and result.app_name:
            return result
        
        # Try Hyprland
        result = self._get_window_hyprland()
        if result and result.app_name:
            return result
        
        # Try KDE
        result = self._get_window_kde()
        if result and result.app_name:
            return result
        
        # Fallback: try to get from focused process
        return self._get_window_fallback()
    
    def _get_window_gnome(self) -> Optional[WindowInfo]:
        """Get active window on GNOME using gdbus."""
        try:
            # Get window title
            stdout, stderr, code = run_command([
                'gdbus', 'call', '--session',
                '--dest', 'org.gnome.Shell',
                '--object-path', '/org/gnome/Shell',
                '--method', 'org.gnome.Shell.Eval',
                '''
                let start_time = Date.now();
                let win = global.display.focus_window;
                let result = {};
                if (win) {
                    result.title = win.get_title() || '';
                    result.wm_class = win.get_wm_class() || '';
                    result.pid = win.get_pid() || 0;
                } else {
                    result.title = '';
                    result.wm_class = '';
                    result.pid = 0;
                }
                JSON.stringify(result);
                '''
            ])
            
            if code == 0 and stdout:
                # Parse the output: (true, '{"title":"...","wm_class":"...","pid":...}')
                import json
                match = re.search(r'\{[^}]+\}', stdout)
                if match:
                    data = json.loads(match.group())
                    
                    window_title = data.get('title', '')
                    wm_class = data.get('wm_class', '')
                    pid = data.get('pid', 0)
                    
                    # Get process info
                    process_name = ""
                    if pid and HAS_PSUTIL:
                        try:
                            proc = psutil.Process(pid)
                            process_name = proc.name()
                        except:
                            pass
                    
                    # Determine app name
                    app_name = wm_class or process_name or self._extract_app_from_title(window_title)
                    
                    # Check if browser
                    is_browser = any(b in app_name.lower() for b in self.BROWSER_NAMES)
                    url = self._extract_url_from_title(window_title) if is_browser else ""
                    
                    return WindowInfo(
                        window_title=window_title,
                        app_name=app_name,
                        wm_class=wm_class,
                        process_name=process_name,
                        process_id=pid,
                        is_browser=is_browser,
                        url=url,
                    )
        except Exception as e:
            logger.debug(f"GNOME detection failed: {e}")
        
        return None
    
    def _get_window_sway(self) -> Optional[WindowInfo]:
        """Get active window on Sway."""
        try:
            stdout, stderr, code = run_command(['swaymsg', '-t', 'get_tree'])
            if code != 0:
                return None
            
            import json
            tree = json.loads(stdout)
            
            def find_focused(node):
                if node.get('focused'):
                    return node
                for child in node.get('nodes', []) + node.get('floating_nodes', []):
                    result = find_focused(child)
                    if result:
                        return result
                return None
            
            focused = find_focused(tree)
            if focused:
                app_id = focused.get('app_id', '') or focused.get('window_properties', {}).get('class', '')
                title = focused.get('name', '')
                pid = focused.get('pid', 0)
                
                is_browser = any(b in app_id.lower() for b in self.BROWSER_NAMES)
                
                return WindowInfo(
                    window_title=title,
                    app_name=app_id,
                    wm_class=app_id,
                    process_id=pid,
                    is_browser=is_browser,
                    url=self._extract_url_from_title(title) if is_browser else "",
                )
        except Exception as e:
            logger.debug(f"Sway detection failed: {e}")
        
        return None
    
    def _get_window_hyprland(self) -> Optional[WindowInfo]:
        """Get active window on Hyprland."""
        try:
            stdout, stderr, code = run_command(['hyprctl', 'activewindow', '-j'])
            if code != 0:
                return None
            
            import json
            data = json.loads(stdout)
            
            wm_class = data.get('class', '')
            title = data.get('title', '')
            pid = data.get('pid', 0)
            
            is_browser = any(b in wm_class.lower() for b in self.BROWSER_NAMES)
            
            return WindowInfo(
                window_title=title,
                app_name=wm_class,
                wm_class=wm_class,
                process_id=pid,
                is_browser=is_browser,
                url=self._extract_url_from_title(title) if is_browser else "",
            )
        except Exception as e:
            logger.debug(f"Hyprland detection failed: {e}")
        
        return None
    
    def _get_window_kde(self) -> Optional[WindowInfo]:
        """Get active window on KDE Plasma."""
        try:
            stdout, stderr, code = run_command([
                'qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.activeClient'
            ])
            # TODO: Implement full KDE support
        except:
            pass
        return None
    
    def _get_window_x11(self) -> Optional[WindowInfo]:
        """Get active window on X11 using xdotool."""
        try:
            # Get window ID
            stdout, stderr, code = run_command(['xdotool', 'getactivewindow'])
            if code != 0:
                return None
            
            window_id = int(stdout.strip())
            
            # Get window name
            stdout, stderr, code = run_command(['xdotool', 'getwindowname', str(window_id)])
            window_title = stdout.strip() if code == 0 else ""
            
            # Get PID
            stdout, stderr, code = run_command(['xdotool', 'getwindowpid', str(window_id)])
            pid = int(stdout.strip()) if code == 0 else 0
            
            # Get WM_CLASS
            wm_class = ""
            stdout, stderr, code = run_command(['xprop', '-id', str(window_id), 'WM_CLASS'])
            if code == 0:
                match = re.search(r'"([^"]+)"', stdout)
                if match:
                    wm_class = match.group(1)
            
            # Get process name
            process_name = ""
            if pid and HAS_PSUTIL:
                try:
                    process_name = psutil.Process(pid).name()
                except:
                    pass
            
            app_name = wm_class or process_name or self._extract_app_from_title(window_title)
            is_browser = any(b in app_name.lower() for b in self.BROWSER_NAMES)
            
            return WindowInfo(
                window_id=window_id,
                window_title=window_title,
                app_name=app_name,
                wm_class=wm_class,
                process_name=process_name,
                process_id=pid,
                is_browser=is_browser,
                url=self._extract_url_from_title(window_title) if is_browser else "",
            )
        except Exception as e:
            logger.debug(f"X11 detection failed: {e}")
        
        return None
    
    def _get_window_fallback(self) -> Optional[WindowInfo]:
        """Fallback method - try to detect from running processes."""
        if not HAS_PSUTIL:
            return WindowInfo(app_name="Unknown")
        
        try:
            # Find the most likely foreground app by checking recent CPU usage
            gui_apps = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    name = proc.info['name'].lower()
                    # Skip system processes
                    if any(x in name for x in ['systemd', 'dbus', 'pulseaudio', 'pipewire', 'xdg', 'gnome-shell']):
                        continue
                    # Look for GUI apps
                    if any(x in name for x in ['firefox', 'chrome', 'code', 'terminal', 'nautilus', 'gedit']):
                        gui_apps.append((proc.info['name'], proc.info['cpu_percent'], proc.info['pid']))
                except:
                    continue
            
            if gui_apps:
                # Get the one with highest CPU (likely active)
                gui_apps.sort(key=lambda x: x[1], reverse=True)
                app_name = gui_apps[0][0]
                pid = gui_apps[0][2]
                is_browser = any(b in app_name.lower() for b in self.BROWSER_NAMES)
                
                return WindowInfo(
                    app_name=app_name,
                    process_name=app_name,
                    process_id=pid,
                    is_browser=is_browser,
                )
        except Exception as e:
            logger.debug(f"Fallback detection failed: {e}")
        
        return WindowInfo(app_name="Unknown")
    
    def _extract_app_from_title(self, title: str) -> str:
        """Try to extract app name from window title."""
        if not title:
            return "Unknown"
        
        # Common patterns: "Title - App Name" or "App Name: Title"
        if " - " in title:
            parts = title.split(" - ")
            return parts[-1].strip()
        elif ": " in title:
            parts = title.split(": ")
            return parts[0].strip()
        
        return title[:30]
    
    def _extract_url_from_title(self, title: str) -> str:
        """Extract URL/domain from browser window title."""
        if not title:
            return ""
        
        title_lower = title.lower()
        
        known_sites = {
            'youtube': 'youtube.com',
            'github': 'github.com',
            'stackoverflow': 'stackoverflow.com',
            'stack overflow': 'stackoverflow.com',
            'reddit': 'reddit.com',
            'twitter': 'twitter.com',
            'facebook': 'facebook.com',
            'linkedin': 'linkedin.com',
            'instagram': 'instagram.com',
            'netflix': 'netflix.com',
            'amazon': 'amazon.com',
            'google': 'google.com',
            'gmail': 'gmail.com',
        }
        
        for name, domain in known_sites.items():
            if name in title_lower:
                return domain
        
        return ""
    
    def is_user_idle(self, threshold: int = 300) -> bool:
        """Check if user is idle."""
        # TODO: Implement idle detection
        return False
    
    def close(self):
        """Cleanup resources."""
        pass


# Singleton
_monitor: Optional[WindowMonitor] = None

def get_window_monitor() -> WindowMonitor:
    global _monitor
    if _monitor is None:
        _monitor = WindowMonitor()
    return _monitor

def get_active_window() -> Optional[WindowInfo]:
    return get_window_monitor().get_active_window()
