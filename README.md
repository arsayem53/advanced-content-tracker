# Advanced Content Tracker

> **"Know exactly what you're watching, reading, and doing - every second."**

A powerful Linux background daemon that captures screenshots, analyzes them using AI/ML, and tells you **exactly** what content you're consuming - not just "YouTube" but "watching romantic music video on YouTube" or "reading Python tutorial on Medium".

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 🎯 Multi-Level Detection

| Level | Detection | Example |
|-------|-----------|---------|
| **1** | Application | VS Code → Python file, Terminal → coding |
| **2** | Website | YouTube, GitHub, LinkedIn, Reddit |
| **3** | Video Content | Cartoon, Music Video, Tutorial, Gaming |
| **4** | Text Content | Article topic, Code language, Document type |
| **5** | NSFW Detection | Adult content with confidence score |
| **6** | Activity Type | Productive, Educational, Entertainment |

### 🧠 Smart Analysis

- **CLIP Model** - AI-powered image+text understanding
- **NudeNet** - NSFW/adult content detection
- **Tesseract OCR** - Text extraction from screenshots
- **Rule-based** - Fast pattern matching for known sites

### 📊 Comprehensive Tracking

- Real-time activity monitoring
- Productivity scoring (-1.0 to +1.0)
- Daily/weekly reports
- Time breakdown by category
- Top apps and websites

### 🔒 Privacy First

- Everything runs **locally** - no data sent anywhere
- Optional screenshot storage
- Configurable exclusion lists
- Password manager detection

## 🚀 Quick Start

# 🚀 Complete Guide: Running Advanced Content Tracker

## 📋 Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [First Run & Testing](#3-first-run--testing)
4. [Daily Usage](#4-daily-usage)
5. [Commands Reference](#5-commands-reference)
6. [Configuration](#6-configuration)
7. [Troubleshooting](#7-troubleshooting)
8. [Tips & Best Practices](#8-tips--best-practices)

---

## 1. Prerequisites

### System Requirements
```bash
# Check your system
uname -a                    # Should be Linux
python3 --version           # Need Python 3.8+
echo $XDG_SESSION_TYPE      # Shows 'x11' or 'wayland'
```

### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    tesseract-ocr-eng \
    xdotool \
    xprintidle \
    scrot \
    libnotify-bin \
    libx11-dev \
    libxext-dev \
    libxss-dev
```

**Fedora:**
```bash
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-virtualenv \
    tesseract \
    tesseract-langpack-eng \
    xdotool \
    xprintidle \
    scrot \
    libnotify \
    libX11-devel \
    libXext-devel \
    libXScrnSaver-devel
```

**Arch Linux:**
```bash
sudo pacman -S \
    python \
    python-pip \
    python-virtualenv \
    tesseract \
    tesseract-data-eng \
    xdotool \
    xorg-xprintidle \
    scrot \
    libnotify \
    libx11 \
    libxext \
    libxss
```

**For Wayland (Sway/GNOME Wayland/Hyprland):**
```bash
# Ubuntu/Debian
sudo apt install -y grim slurp wl-clipboard

# Fedora
sudo dnf install -y grim slurp wl-clipboard

# Arch
sudo pacman -S grim slurp wl-clipboard
```

---

## 2. Installation

### Step 1: Navigate to Project Directory
```bash
cd ~/Desktop/advanced-content-tracker
# or wherever your project is located
```

### Step 2: Make Scripts Executable
```bash
chmod +x install.sh
chmod +x install_service.sh
chmod +x main.py
chmod +x scripts/*.py
chmod +x models/download_models.py
```

### Step 3: Run the Installer
```bash
./install.sh
```

This will:
- ✅ Detect your package manager
- ✅ Install system dependencies
- ✅ Create Python virtual environment
- ✅ Install Python packages
- ✅ Create necessary directories
- ✅ Optionally download ML models

### Step 4: Manual Installation (If install.sh fails)
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip wheel setuptools

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/screenshots data/reports logs models/clip models/nudenet
```

### Step 5: Verify Installation
```bash
# Activate virtual environment
source venv/bin/activate

# Check if imports work
python3 -c "from src.core.daemon import ContentTrackerDaemon; print('✅ Installation successful!')"
```

---

## 3. First Run & Testing

### Activate Virtual Environment (Always do this first!)
```bash
cd ~/Desktop/advanced-content-tracker
source venv/bin/activate
```

You'll see `(venv)` in your terminal prompt.

### Run Detection Test
```bash
python main.py --test
```

Expected output:
```
╔═══════════════════════════════════════════════════════════╗
║          Content Tracker - Detection Test Suite           ║
╚═══════════════════════════════════════════════════════════╝

==================================================
Testing Screenshot Capture
==================================================
   ✅ Screenshot captured: 1920x1080

==================================================
Testing Window Monitor
==================================================
   ✅ Window detected in 15.2ms:
      App: Firefox
      Title: GitHub - Advanced Content Tracker...
      Process: firefox (PID: 12345)

==================================================
Testing OCR
==================================================
   ✅ OCR Extracted 847 characters

... (more tests)

==================================================
All tests completed!
==================================================
```

### Run Quick Benchmark
```bash
python scripts/benchmark.py --quick
```

---

## 4. Daily Usage

### Start Tracking (Foreground Mode)
```bash
# Activate venv first
source venv/bin/activate

# Start tracking (see output in terminal)
python main.py
```

Press `Ctrl+C` to stop.

### Start Tracking (Background/Daemon Mode)
```bash
source venv/bin/activate

# Start in background
python main.py --daemon

# Check if running
python main.py --status

# Stop when done
python main.py --stop
```

### View Live Status
```bash
python main.py --status
```

Output:
```
📊 Content Tracker Status
========================================
  Status: 🟢 Running
  Uptime: 2h 34m
  Captures: 287
  Analyses: 285
  Errors: 0
  Queue Size: 0

  Last Activity:
    App: VS Code
    Window: main.py - content-tracker

📁 Database Statistics
========================================
  Activities: 1,247
  Daily Stats: 5
  Size: 2.45 MB
```

### Generate Reports
```bash
# Today's report
python main.py --report

# Yesterday's report
python main.py --report yesterday

# Specific date
python main.py --report 2024-01-15
```

Output:
```
📊 Activity Report for 2024-01-20
==================================================

⏱️  Total Tracked Time: 6h 45m
📈 Productivity Score: 72.3/100
🔢 Total Sessions: 812

📂 Time by Activity Type:
----------------------------------------
  💻 Productive          3h 20m ████████████░░░░░░░░ 49.4%
  📖 Educational           45m ███░░░░░░░░░░░░░░░░░ 11.1%
  🎬 Entertainment       1h 30m ██████░░░░░░░░░░░░░░ 22.2%
  📱 Social Media          30m ██░░░░░░░░░░░░░░░░░░  7.4%
  ⚪ Neutral               40m ███░░░░░░░░░░░░░░░░░  9.9%

🏆 Top Applications:
----------------------------------------
  1. VS Code                        2h 15m
  2. Firefox                        1h 45m
  3. Terminal                         45m

🌐 Top Websites:
----------------------------------------
  1. github.com                       45m
  2. youtube.com                      30m
  3. stackoverflow.com                20m
```

---

## 5. Commands Reference

### Main Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Start tracking (foreground) |
| `python main.py --daemon` | Start as background daemon |
| `python main.py --status` | Show current status |
| `python main.py --stop` | Stop the daemon |
| `python main.py --report` | Generate today's report |
| `python main.py --report yesterday` | Yesterday's report |
| `python main.py --report 2024-01-15` | Specific date report |
| `python main.py --test` | Run detection tests |
| `python main.py --version` | Show version info |
| `python main.py --help` | Show all options |

### Additional Options

| Option | Description |
|--------|-------------|
| `--config FILE` | Use custom config file |
| `--log-level DEBUG` | Set log level (DEBUG/INFO/WARNING/ERROR) |
| `--no-ml` | Disable ML models (faster, less accurate) |

### Utility Scripts

```bash
# Analyze historical data
python scripts/analyze_history.py --days 7

# Run performance benchmarks
python scripts/benchmark.py

# Test detection on current screen
python scripts/test_detection.py

# Download/verify ML models
python models/download_models.py --verify
python models/download_models.py --download
```

---

## 6. Configuration

### Edit Configuration
```bash
# Open config file in your editor
nano config.yaml
# or
code config.yaml
```

### Key Settings to Customize

```yaml
# config.yaml

# How often to capture (seconds)
monitoring:
  screenshot_interval: 30    # Capture every 30 seconds
  idle_threshold: 300        # Consider idle after 5 minutes

# Enable/disable detection methods
detection:
  use_clip: true             # AI image classification (slower but accurate)
  use_nudenet: true          # NSFW detection
  use_ocr: true              # Text extraction
  use_rules: true            # Fast rule-based detection

# Privacy settings
privacy:
  store_screenshots: false   # Don't save screenshots
  excluded_apps:             # Don't track these apps
    - keepassxc
    - bitwarden
  excluded_title_keywords:   # Skip windows with these in title
    - password
    - private

# Notifications
notifications:
  enabled: true
  distraction_threshold: 1800  # Alert after 30 min entertainment

# Productivity weights
scoring:
  weights:
    productive: 1.0
    educational: 0.8
    entertainment: -0.3
    social_media: -0.4
    gaming: -0.3
```

### Performance Tuning

**For slower computers (disable ML):**
```yaml
detection:
  use_clip: false
  use_nudenet: false
  use_ocr: true
  use_rules: true

performance:
  enable_gpu: false
  max_memory_mb: 1024
```

**For powerful computers (full ML):**
```yaml
detection:
  use_clip: true
  use_nudenet: true
  use_ocr: true

performance:
  enable_gpu: true   # If you have NVIDIA GPU with CUDA
  max_memory_mb: 4096
  cache_models: true
```

---

## 7. Troubleshooting

### Common Issues & Solutions

#### Issue: "No module named 'src'"
```bash
# Make sure you're in the project directory
cd ~/Desktop/advanced-content-tracker

# Make sure venv is activated
source venv/bin/activate

# Check the prompt shows (venv)
```

#### Issue: Screenshot capture fails
```bash
# For X11
sudo apt install scrot xdotool
scrot /tmp/test.png && echo "Screenshot works!"

# For Wayland
sudo apt install grim
grim /tmp/test.png && echo "Screenshot works!"

# Check display server
echo $XDG_SESSION_TYPE
```

#### Issue: OCR not working
```bash
# Install Tesseract
sudo apt install tesseract-ocr tesseract-ocr-eng

# Verify installation
tesseract --version
tesseract --list-langs
```

#### Issue: Permission denied for idle detection
```bash
# Add user to input group
sudo usermod -a -G input $USER

# Log out and log back in
# Then verify
groups | grep input
```

#### Issue: Database locked
```bash
# Stop any running instances
python main.py --stop
pkill -f "python.*main.py"

# Remove lock file if exists
rm -f data/activity.db-wal data/activity.db-shm

# Restart
python main.py
```

#### Issue: High CPU/Memory usage
```bash
# Disable ML models in config.yaml
detection:
  use_clip: false
  use_nudenet: false

# Increase screenshot interval
monitoring:
  screenshot_interval: 60  # Every minute instead of 30 seconds
```

#### Issue: Module import errors
```bash
# Reinstall requirements
source venv/bin/activate
pip install --upgrade -r requirements.txt

# If specific module missing
pip install <module_name>
```

### View Logs
```bash
# View application logs
tail -f logs/app.log

# View last 100 lines
tail -100 logs/app.log

# Search for errors
grep -i error logs/app.log
```

### Reset Everything
```bash
# Stop daemon
python main.py --stop

# Remove database (loses all history!)
rm -f data/activity.db*

# Remove logs
rm -f logs/*.log

# Restart fresh
python main.py --test
python main.py
```

---

## 8. Tips & Best Practices

### 🎯 For Best Results

1. **Start with testing:**
   ```bash
   python main.py --test
   ```
   Make sure all tests pass before running the daemon.

2. **Run in foreground first:**
   ```bash
   python main.py
   ```
   Watch the output to ensure it's working correctly.

3. **Check status regularly:**
   ```bash
   python main.py --status
   ```

4. **Review daily reports:**
   ```bash
   python main.py --report
   ```

### 🔒 Privacy Recommendations

1. **Disable screenshot storage:**
   ```yaml
   privacy:
     store_screenshots: false
   ```

2. **Exclude sensitive apps:**
   ```yaml
   privacy:
     excluded_apps:
       - keepassxc
       - bitwarden
       - 1password
       - signal
   ```

3. **Enable data retention:**
   ```yaml
   privacy:
     data_retention_days: 30  # Auto-delete after 30 days
   ```

### ⚡ Performance Tips

1. **Increase interval for less CPU usage:**
   ```yaml
   monitoring:
     screenshot_interval: 60  # Every minute
   ```

2. **Disable unused detection methods:**
   ```yaml
   detection:
     use_clip: false      # Disable if not needed
     use_nudenet: false   # Disable if not needed
   ```

3. **Clean old data periodically:**
   ```bash
   python -c "from src.storage.database import get_database; db = get_database(); db.cleanup_old_data(30)"
   ```

### 🖥️ Run as System Service (Auto-start on boot)

```bash
# Install as systemd service
./install_service.sh

# Service commands
systemctl --user start content-tracker
systemctl --user stop content-tracker
systemctl --user status content-tracker
systemctl --user restart content-tracker

# View service logs
journalctl --user -u content-tracker -f

# Disable auto-start
systemctl --user disable content-tracker
```

### 📊 Analyze Your History

```bash
# Last 7 days analysis
python scripts/analyze_history.py --days 7

# Last month
python scripts/analyze_history.py --days 30

# Export to JSON
python scripts/analyze_history.py --days 7 --format json --output report.json

# Filter by category
python scripts/analyze_history.py --days 7 --productive-only
```

---

## 🎉 Quick Start Cheat Sheet

```bash
# 1. Go to project directory
cd ~/Desktop/advanced-content-tracker

# 2. Activate virtual environment
source venv/bin/activate

# 3. Test everything works
python main.py --test

# 4. Start tracking
python main.py              # Foreground (see output)
# OR
python main.py --daemon     # Background (silent)

# 5. Check status
python main.py --status

# 6. Generate report
python main.py --report

# 7. Stop tracking
python main.py --stop       # If running as daemon
# OR
Ctrl+C                      # If running in foreground

# 8. Deactivate venv when done
deactivate
```

---

##  Need Help?

1. **Check logs:** `tail -f logs/app.log`
2. **Run tests:** `python main.py --test`
3. **Enable debug logging:**
   ```yaml
   general:
     log_level: "DEBUG"
   ```
4. **Check the README:** `cat README.md`

---

**Happy Tracking! 🎯📊**
