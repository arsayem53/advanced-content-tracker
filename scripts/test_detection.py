#!/usr/bin/env python3
"""
Test script for detection capabilities.
Run this to verify all detection components are working.
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logging
from src.utils.config import get_config


def test_screenshot():
    """Test screenshot capture."""
    print("\n" + "="*50)
    print("Testing Screenshot Capture")
    print("="*50)
    
    from src.core.screenshot import get_screenshot_capture
    
    capture = get_screenshot_capture()
    print(f"Display server: {capture._display_server}")
    print(f"Capture method: {capture._capture_method}")
    
    start = time.time()
    screenshot = capture.capture()
    elapsed = (time.time() - start) * 1000
    
    if screenshot:
        print(f"✅ Captured: {screenshot.size[0]}x{screenshot.size[1]} in {elapsed:.1f}ms")
        return screenshot
    else:
        print("❌ Capture failed")
        return None


def test_window_monitor():
    """Test window monitoring."""
    print("\n" + "="*50)
    print("Testing Window Monitor")
    print("="*50)
    
    from src.core.monitor import get_window_monitor
    
    monitor = get_window_monitor()
    print(f"Display server: {monitor._display_server}")
    
    start = time.time()
    window = monitor.get_active_window()
    elapsed = (time.time() - start) * 1000
    
    if window:
        print(f"✅ Window detected in {elapsed:.1f}ms:")
        print(f"   App: {window.app_name}")
        print(f"   Title: {window.window_title[:60]}...")
        print(f"   Process: {window.process_name} (PID: {window.process_id})")
        print(f"   WM Class: {window.wm_class}")
        print(f"   Is Browser: {window.is_browser}")
        if window.url:
            print(f"   URL: {window.url}")
        return window
    else:
        print("❌ Window detection failed")
        return None


def test_ocr(screenshot):
    """Test OCR extraction."""
    print("\n" + "="*50)
    print("Testing OCR")
    print("="*50)
    
    if screenshot is None:
        print("⚠️ Skipping - no screenshot available")
        return None
    
    from src.analyzers.ocr_analyzer import OCRAnalyzer
    
    ocr = OCRAnalyzer()
    
    start = time.time()
    text = ocr.extract_text(screenshot)
    elapsed = (time.time() - start) * 1000
    
    if text:
        print(f"✅ Extracted {len(text)} chars in {elapsed:.1f}ms")
        print(f"   Preview: {text[:100]}...")
        
        # Analyze text
        analysis = ocr.analyze_text(text)
        if analysis:
            print(f"   Keywords: {analysis.get('keywords', [])[:5]}")
            print(f"   Language: {analysis.get('language', 'unknown')}")
        
        return text
    else:
        print(f"⚠️ No text extracted (might be normal) in {elapsed:.1f}ms")
        return ""


def test_app_detector(window):
    """Test app detection."""
    print("\n" + "="*50)
    print("Testing App Detector")
    print("="*50)
    
    from src.detectors.app_detector import AppDetector
    
    detector = AppDetector()
    
    if window:
        result = detector.detect(
            window.process_name,
            window.wm_class,
            window.window_title
        )
        
        print(f"✅ Detection result:")
        print(f"   App Name: {result['app_name']}")
        print(f"   Category: {result['category']}")
        print(f"   Activity: {result['activity_type']}")
        print(f"   Is Browser: {result['is_browser']}")
        print(f"   Is IDE: {result['is_ide']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        
        return result
    else:
        print("⚠️ Skipping - no window info")
        return None


def test_website_detector(window):
    """Test website detection."""
    print("\n" + "="*50)
    print("Testing Website Detector")
    print("="*50)
    
    from src.detectors.website_detector import WebsiteDetector
    
    detector = WebsiteDetector()
    
    # Test with sample URLs
    test_urls = [
        "https://github.com/user/repo",
        "https://www.youtube.com/watch?v=abc123",
        "https://twitter.com/user",
        "https://stackoverflow.com/questions/123",
    ]
    
    for url in test_urls:
        result = detector.detect(url)
        print(f"   {url[:40]:40} -> {result['category']:15} ({result['activity_type']})")
    
    # Test with actual window if browser
    if window and window.is_browser and window.url:
        print(f"\n   Current browser URL:")
        result = detector.detect(window.url, window.window_title)
        print(f"   {window.url[:50]}")
        print(f"   Category: {result['category']}")
        print(f"   Activity: {result['activity_type']}")
        print(f"   Is NSFW: {result['is_nsfw']}")
    
    return True


def test_video_detector():
    """Test video content detection."""
    print("\n" + "="*50)
    print("Testing Video Detector")
    print("="*50)
    
    from src.detectors.video_detector import VideoDetector
    
    detector = VideoDetector()
    
    # Test with sample titles
    test_titles = [
        "Python Tutorial for Beginners - Full Course",
        "Minecraft Let's Play Episode 25",
        "Official Music Video - Popular Song",
        "Attack on Titan Episode 1 [Subbed]",
        "Stand-up Comedy Special - Netflix",
        "How to Build a PC - Step by Step Guide",
        "🔴 LIVE: Gaming Stream",
        "Documentary: The History of Space Exploration",
    ]
    
    for title in test_titles:
        result = detector.detect(title)
        print(f"   {result['video_type']:15} <- {title[:45]}...")
    
    return True


def test_activity_detector(window):
    """Test high-level activity detection."""
    print("\n" + "="*50)
    print("Testing Activity Detector")
    print("="*50)
    
    from src.detectors.activity_detector import ActivityDetector
    
    detector = ActivityDetector()
    
    if window:
        result = detector.detect(
            app_name=window.app_name,
            process_name=window.process_name,
            window_title=window.window_title,
            url=window.url,
            wm_class=window.wm_class,
            is_browser=window.is_browser
        )
        
        print(f"✅ Activity Detection Result:")
        print(f"   Type: {result.activity_type}")
        print(f"   Category: {result.category}")
        print(f"   Description: {result.description}")
        print(f"   Is Productive: {result.is_productive}")
        print(f"   Productivity Score: {result.productivity_score:+.1f}")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Summary: {detector.get_activity_summary(result)}")
        
        return result
    else:
        print("⚠️ Skipping - no window info")
        return None


def test_content_classifier(screenshot, window):
    """Test full content classification."""
    print("\n" + "="*50)
    print("Testing Content Classifier")
    print("="*50)
    
    if screenshot is None:
        print("⚠️ Skipping - no screenshot")
        return None
    
    from src.analyzers.content_classifier import ContentClassifier
    
    classifier = ContentClassifier()
    
    start = time.time()
    result = classifier.classify(screenshot, window)
    elapsed = (time.time() - start) * 1000
    
    print(f"✅ Classification completed in {elapsed:.1f}ms:")
    print(f"   Content Type: {result.get('content_type', 'unknown')}")
    print(f"   Category: {result.get('content_category', 'unknown')}")
    print(f"   Activity Type: {result.get('activity_type', 'unknown')}")
    print(f"   Description: {result.get('content_description', 'N/A')}")
    print(f"   Is Productive: {result.get('is_productive', False)}")
    print(f"   Productivity Score: {result.get('productivity_score', 0):+.1f}")
    print(f"   Confidence: {result.get('confidence', 0):.1%}")
    print(f"   Detection Method: {result.get('detection_method', 'unknown')}")
    print(f"   Is NSFW: {result.get('is_nsfw', False)}")
    
    return result


def test_database():
    """Test database operations."""
    print("\n" + "="*50)
    print("Testing Database")
    print("="*50)
    
    from src.storage.database import get_database
    from src.storage.models import Activity
    from datetime import datetime
    
    db = get_database()
    
    # Test insert
    test_activity = Activity(
        timestamp=datetime.now(),
        app_name="Test App",
        window_title="Test Window",
        activity_type="productive",
        content_type="test",
        content_description="Test activity for detection testing",
        confidence=0.99,
        duration=30
    )
    
    activity_id = db.insert_activity(test_activity)
    print(f"✅ Inserted test activity (ID: {activity_id})")
    
    # Test query
    recent = db.get_recent_activities(hours=1)
    print(f"✅ Found {len(recent)} recent activities")
    
    # Test stats
    counts = db.get_record_count()
    print(f"✅ Database stats:")
    print(f"   Activities: {counts.get('activities', 0)}")
    print(f"   Daily Stats: {counts.get('daily_stats', 0)}")
    print(f"   Size: {db.get_database_size() / 1024:.1f} KB")
    
    return True


def main():
    """Run all tests."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          Content Tracker - Detection Test Suite           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Setup logging
    setup_logging(level='WARNING')
    
    # Run tests
    screenshot = test_screenshot()
    window = test_window_monitor()
    test_ocr(screenshot)
    test_app_detector(window)
    test_website_detector(window)
    test_video_detector()
    test_activity_detector(window)
    test_content_classifier(screenshot, window)
    test_database()
    
    print("\n" + "="*50)
    print("All tests completed!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
