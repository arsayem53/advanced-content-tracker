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

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/content-tracker.git
cd content-tracker

# Run installer
chmod +x install.sh
./install.sh
