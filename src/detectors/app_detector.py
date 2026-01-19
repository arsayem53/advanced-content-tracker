"""
App Detector - Detects and classifies applications.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AppDetector:
    """
    Detects what application is being used and classifies it.
    """
    
    # Default app classifications
    DEFAULT_APP_RULES = {
        # Code editors / IDEs
        "code": {"category": "coding", "activity": "productive", "name": "VS Code"},
        "code-oss": {"category": "coding", "activity": "productive", "name": "VS Code OSS"},
        "codium": {"category": "coding", "activity": "productive", "name": "VSCodium"},
        "sublime_text": {"category": "coding", "activity": "productive", "name": "Sublime Text"},
        "atom": {"category": "coding", "activity": "productive", "name": "Atom"},
        "idea": {"category": "coding", "activity": "productive", "name": "IntelliJ IDEA"},
        "pycharm": {"category": "coding", "activity": "productive", "name": "PyCharm"},
        "webstorm": {"category": "coding", "activity": "productive", "name": "WebStorm"},
        "android-studio": {"category": "coding", "activity": "productive", "name": "Android Studio"},
        "eclipse": {"category": "coding", "activity": "productive", "name": "Eclipse"},
        "netbeans": {"category": "coding", "activity": "productive", "name": "NetBeans"},
        "vim": {"category": "coding", "activity": "productive", "name": "Vim"},
        "nvim": {"category": "coding", "activity": "productive", "name": "Neovim"},
        "emacs": {"category": "coding", "activity": "productive", "name": "Emacs"},
        "gedit": {"category": "text_editing", "activity": "productive", "name": "gedit"},
        "kate": {"category": "text_editing", "activity": "productive", "name": "Kate"},
        "nano": {"category": "text_editing", "activity": "productive", "name": "nano"},
        
        # Terminals
        "gnome-terminal": {"category": "terminal", "activity": "productive", "name": "Terminal"},
        "konsole": {"category": "terminal", "activity": "productive", "name": "Konsole"},
        "xterm": {"category": "terminal", "activity": "productive", "name": "XTerm"},
        "alacritty": {"category": "terminal", "activity": "productive", "name": "Alacritty"},
        "kitty": {"category": "terminal", "activity": "productive", "name": "Kitty"},
        "tilix": {"category": "terminal", "activity": "productive", "name": "Tilix"},
        "terminator": {"category": "terminal", "activity": "productive", "name": "Terminator"},
        "urxvt": {"category": "terminal", "activity": "productive", "name": "URxvt"},
        "st": {"category": "terminal", "activity": "productive", "name": "st"},
        "wezterm": {"category": "terminal", "activity": "productive", "name": "WezTerm"},
        
        # Browsers
        "firefox": {"category": "browser", "activity": "neutral", "name": "Firefox"},
        "firefox-esr": {"category": "browser", "activity": "neutral", "name": "Firefox ESR"},
        "chrome": {"category": "browser", "activity": "neutral", "name": "Chrome"},
        "chromium": {"category": "browser", "activity": "neutral", "name": "Chromium"},
        "google-chrome": {"category": "browser", "activity": "neutral", "name": "Google Chrome"},
        "brave": {"category": "browser", "activity": "neutral", "name": "Brave"},
        "opera": {"category": "browser", "activity": "neutral", "name": "Opera"},
        "vivaldi": {"category": "browser", "activity": "neutral", "name": "Vivaldi"},
        "microsoft-edge": {"category": "browser", "activity": "neutral", "name": "Edge"},
        "epiphany": {"category": "browser", "activity": "neutral", "name": "GNOME Web"},
        "librewolf": {"category": "browser", "activity": "neutral", "name": "LibreWolf"},
        "qutebrowser": {"category": "browser", "activity": "neutral", "name": "qutebrowser"},
        
        # Office / Productivity
        "libreoffice": {"category": "office", "activity": "productive", "name": "LibreOffice"},
        "soffice": {"category": "office", "activity": "productive", "name": "LibreOffice"},
        "libreoffice-writer": {"category": "document", "activity": "productive", "name": "LibreOffice Writer"},
        "libreoffice-calc": {"category": "spreadsheet", "activity": "productive", "name": "LibreOffice Calc"},
        "libreoffice-impress": {"category": "presentation", "activity": "productive", "name": "LibreOffice Impress"},
        "onlyoffice": {"category": "office", "activity": "productive", "name": "OnlyOffice"},
        "wps": {"category": "office", "activity": "productive", "name": "WPS Office"},
        
        # PDF / Document Viewers
        "evince": {"category": "document_viewer", "activity": "neutral", "name": "Document Viewer"},
        "okular": {"category": "document_viewer", "activity": "neutral", "name": "Okular"},
        "zathura": {"category": "document_viewer", "activity": "neutral", "name": "Zathura"},
        "mupdf": {"category": "document_viewer", "activity": "neutral", "name": "MuPDF"},
        "xreader": {"category": "document_viewer", "activity": "neutral", "name": "Xreader"},
        "atril": {"category": "document_viewer", "activity": "neutral", "name": "Atril"},
        
        # File Managers
        "nautilus": {"category": "file_manager", "activity": "neutral", "name": "Files"},
        "dolphin": {"category": "file_manager", "activity": "neutral", "name": "Dolphin"},
        "thunar": {"category": "file_manager", "activity": "neutral", "name": "Thunar"},
        "pcmanfm": {"category": "file_manager", "activity": "neutral", "name": "PCManFM"},
        "nemo": {"category": "file_manager", "activity": "neutral", "name": "Nemo"},
        "caja": {"category": "file_manager", "activity": "neutral", "name": "Caja"},
        "ranger": {"category": "file_manager", "activity": "neutral", "name": "Ranger"},
        
        # Media Players
        "vlc": {"category": "video_player", "activity": "entertainment", "name": "VLC"},
        "mpv": {"category": "video_player", "activity": "entertainment", "name": "mpv"},
        "totem": {"category": "video_player", "activity": "entertainment", "name": "Videos"},
        "celluloid": {"category": "video_player", "activity": "entertainment", "name": "Celluloid"},
        "smplayer": {"category": "video_player", "activity": "entertainment", "name": "SMPlayer"},
        "parole": {"category": "video_player", "activity": "entertainment", "name": "Parole"},
        "kodi": {"category": "media_center", "activity": "entertainment", "name": "Kodi"},
        
        # Music Players
        "spotify": {"category": "music", "activity": "entertainment", "name": "Spotify"},
        "rhythmbox": {"category": "music", "activity": "entertainment", "name": "Rhythmbox"},
        "clementine": {"category": "music", "activity": "entertainment", "name": "Clementine"},
        "audacious": {"category": "music", "activity": "entertainment", "name": "Audacious"},
        "lollypop": {"category": "music", "activity": "entertainment", "name": "Lollypop"},
        "cmus": {"category": "music", "activity": "entertainment", "name": "cmus"},
        
        # Image Viewers/Editors
        "eog": {"category": "image_viewer", "activity": "neutral", "name": "Image Viewer"},
        "feh": {"category": "image_viewer", "activity": "neutral", "name": "feh"},
        "sxiv": {"category": "image_viewer", "activity": "neutral", "name": "sxiv"},
        "gimp": {"category": "image_editing", "activity": "productive", "name": "GIMP"},
        "inkscape": {"category": "design", "activity": "productive", "name": "Inkscape"},
        "krita": {"category": "design", "activity": "productive", "name": "Krita"},
        "darktable": {"category": "photo_editing", "activity": "productive", "name": "Darktable"},
        
        # Communication
        "slack": {"category": "communication", "activity": "neutral", "name": "Slack"},
        "discord": {"category": "communication", "activity": "social_media", "name": "Discord"},
        "telegram-desktop": {"category": "communication", "activity": "social_media", "name": "Telegram"},
        "signal-desktop": {"category": "communication", "activity": "neutral", "name": "Signal"},
        "element": {"category": "communication", "activity": "neutral", "name": "Element"},
        "thunderbird": {"category": "email", "activity": "productive", "name": "Thunderbird"},
        "evolution": {"category": "email", "activity": "productive", "name": "Evolution"},
        "geary": {"category": "email", "activity": "productive", "name": "Geary"},
        "zoom": {"category": "video_call", "activity": "productive", "name": "Zoom"},
        "teams": {"category": "video_call", "activity": "productive", "name": "Teams"},
        "skype": {"category": "video_call", "activity": "neutral", "name": "Skype"},
        
        # Gaming
        "steam": {"category": "gaming", "activity": "gaming", "name": "Steam"},
        "lutris": {"category": "gaming", "activity": "gaming", "name": "Lutris"},
        "heroic": {"category": "gaming", "activity": "gaming", "name": "Heroic Launcher"},
        "retroarch": {"category": "gaming", "activity": "gaming", "name": "RetroArch"},
        "minecraft": {"category": "gaming", "activity": "gaming", "name": "Minecraft"},
        
        # System Tools
        "gnome-control-center": {"category": "settings", "activity": "neutral", "name": "Settings"},
        "systemsettings": {"category": "settings", "activity": "neutral", "name": "System Settings"},
        "gnome-system-monitor": {"category": "system", "activity": "neutral", "name": "System Monitor"},
        "htop": {"category": "system", "activity": "neutral", "name": "htop"},
        "btop": {"category": "system", "activity": "neutral", "name": "btop"},
        
        # Note Taking
        "obsidian": {"category": "notes", "activity": "productive", "name": "Obsidian"},
        "notion": {"category": "notes", "activity": "productive", "name": "Notion"},
        "joplin": {"category": "notes", "activity": "productive", "name": "Joplin"},
        "standard-notes": {"category": "notes", "activity": "productive", "name": "Standard Notes"},
        "simplenote": {"category": "notes", "activity": "productive", "name": "Simplenote"},
        "zettlr": {"category": "notes", "activity": "productive", "name": "Zettlr"},
        
        # 3D / Video Editing
        "blender": {"category": "3d_modeling", "activity": "productive", "name": "Blender"},
        "kdenlive": {"category": "video_editing", "activity": "productive", "name": "Kdenlive"},
        "shotcut": {"category": "video_editing", "activity": "productive", "name": "Shotcut"},
        "openshot": {"category": "video_editing", "activity": "productive", "name": "OpenShot"},
        "davinci-resolve": {"category": "video_editing", "activity": "productive", "name": "DaVinci Resolve"},
        "audacity": {"category": "audio_editing", "activity": "productive", "name": "Audacity"},
    }
    
    def __init__(self, rules_path: str = None):
        """
        Initialize app detector.
        
        Args:
            rules_path: Path to custom rules JSON file
        """
        self.rules = self.DEFAULT_APP_RULES.copy()
        
        # Load custom rules if provided
        if rules_path and os.path.exists(rules_path):
            try:
                with open(rules_path, 'r') as f:
                    custom_rules = json.load(f)
                self.rules.update(custom_rules)
                logger.info(f"Loaded {len(custom_rules)} custom app rules")
            except Exception as e:
                logger.error(f"Failed to load custom app rules: {e}")
    
    def detect(self, process_name: str, wm_class: str = "", window_title: str = "") -> Dict[str, Any]:
        """
        Detect and classify an application.
        
        Args:
            process_name: Process name
            wm_class: Window manager class
            window_title: Window title
            
        Returns:
            Dict with detection results
        """
        result = {
            "app_name": "",
            "category": "unknown",
            "activity_type": "neutral",
            "is_browser": False,
            "is_media_player": False,
            "is_ide": False,
            "is_terminal": False,
            "is_game": False,
            "confidence": 0.5
        }
        
        # Normalize inputs
        process_lower = process_name.lower() if process_name else ""
        wm_class_lower = wm_class.lower() if wm_class else ""
        
        # Try to match by process name first
        for key, info in self.rules.items():
            if key in process_lower or key in wm_class_lower:
                result["app_name"] = info.get("name", process_name)
                result["category"] = info.get("category", "unknown")
                result["activity_type"] = info.get("activity", "neutral")
                result["confidence"] = 0.9
                break
        
        # If no match, try partial matching
        if result["app_name"] == "":
            result["app_name"] = self._guess_app_name(process_name, wm_class)
            result["confidence"] = 0.5
        
        # Set boolean flags
        result["is_browser"] = result["category"] == "browser"
        result["is_media_player"] = result["category"] in ["video_player", "music", "media_center"]
        result["is_ide"] = result["category"] == "coding"
        result["is_terminal"] = result["category"] == "terminal"
        result["is_game"] = result["category"] == "gaming"
        
        # Check for specific patterns in window title
        if window_title:
            result = self._enhance_with_title(result, window_title)
        
        return result
    
    def _guess_app_name(self, process_name: str, wm_class: str) -> str:
        """Guess app name from process name or WM class."""
        if wm_class:
            # WM_CLASS often has a cleaner name
            return wm_class.replace("-", " ").replace("_", " ").title()
        elif process_name:
            return process_name.replace("-", " ").replace("_", " ").title()
        return "Unknown"
    
    def _enhance_with_title(self, result: Dict, title: str) -> Dict:
        """Enhance detection based on window title."""
        title_lower = title.lower()
        
        # Detect if it's a development environment
        if any(ext in title_lower for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']):
            result["category"] = "coding"
            result["activity_type"] = "productive"
            result["is_ide"] = True
        
        # Detect documentation/learning
        if any(word in title_lower for word in ['documentation', 'docs', 'tutorial', 'learn', 'course']):
            result["activity_type"] = "educational"
        
        return result
    
    def is_productive_app(self, process_name: str) -> bool:
        """Quick check if app is considered productive."""
        detection = self.detect(process_name, "", "")
        return detection["activity_type"] == "productive"
    
    def get_app_category(self, process_name: str) -> str:
        """Get category for an app."""
        detection = self.detect(process_name, "", "")
        return detection["category"]
