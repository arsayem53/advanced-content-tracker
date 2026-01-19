#!/usr/bin/env python3
"""
Advanced Content Tracker - Main Entry Point
A Linux background daemon that tracks and classifies your digital activities.

Usage:
    python main.py                    # Start daemon (foreground)
    python main.py --daemon           # Start as background daemon
    python main.py --status           # Show current status
    python main.py --stop             # Stop running daemon
    python main.py --report           # Generate daily report
    python main.py --test             # Run detection test
"""

import os
import sys
import argparse
import signal
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.daemon import ContentTrackerDaemon, get_daemon, start_daemon, stop_daemon
from src.utils.config import get_config, load_config
from src.utils.logger import setup_logging, get_logger
from src.storage.database import get_database


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Advanced Content Tracker - Know exactly what you're watching, reading, and doing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s                     Start tracking (foreground)
    %(prog)s --daemon            Start as background service
    %(prog)s --status            Show tracking status
    %(prog)s --stop              Stop the tracker
    %(prog)s --report today      Generate today's report
    %(prog)s --test              Test detection capabilities
    %(prog)s --config my.yaml    Use custom config file
        """
    )
    
    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--daemon', '-d',
        action='store_true',
        help='Run as background daemon'
    )
    mode_group.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show current tracking status'
    )
    mode_group.add_argument(
        '--stop',
        action='store_true',
        help='Stop running daemon'
    )
    mode_group.add_argument(
        '--report', '-r',
        nargs='?',
        const='today',
        metavar='DATE',
        help='Generate activity report (default: today)'
    )
    mode_group.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run detection test'
    )
    mode_group.add_argument(
        '--version', '-v',
        action='store_true',
        help='Show version information'
    )
    
    # Configuration
    parser.add_argument(
        '--config', '-c',
        metavar='FILE',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=None,
        help='Override log level'
    )
    parser.add_argument(
        '--no-ml',
        action='store_true',
        help='Disable ML-based detection (faster, less accurate)'
    )
    
    return parser.parse_args()


def show_version():
    """Display version information."""
    config = get_config()
    print(f"""
Advanced Content Tracker
========================
Version: {config.get('general.version', '1.0.0')}
Python: {sys.version.split()[0]}
Platform: {sys.platform}

A Linux background daemon that tracks and classifies your digital activities.
Monitors what you're watching, reading, and doing - every second.
    """)


def show_status():
    """Display current tracking status."""
    try:
        daemon = get_daemon()
        status = daemon.get_status()
        
        print("\n📊 Content Tracker Status")
        print("=" * 40)
        
        if status['is_running']:
            print(f"  Status: 🟢 Running")
            print(f"  Uptime: {status['uptime']}")
            print(f"  Captures: {status['total_captures']}")
            print(f"  Analyses: {status['total_analyses']}")
            print(f"  Errors: {status['errors']}")
            print(f"  Queue Size: {status['queue_size']}")
            
            if status['last_window']:
                print(f"\n  Last Activity:")
                print(f"    App: {status['last_window'].get('app_name', 'N/A')}")
                print(f"    Window: {status['last_window'].get('window_title', 'N/A')[:50]}")
        else:
            print(f"  Status: 🔴 Not Running")
        
        # Database stats
        db = get_database()
        counts = db.get_record_count()
        print(f"\n📁 Database Statistics")
        print("=" * 40)
        print(f"  Activities: {counts.get('activities', 0)}")
        print(f"  Daily Stats: {counts.get('daily_stats', 0)}")
        print(f"  Size: {db.get_database_size() / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        sys.exit(1)


def generate_report(date_str: str = 'today'):
    """Generate and display activity report."""
    from datetime import datetime, timedelta
    from src.analytics.stats import StatsCalculator
    from src.analytics.reports import ReportGenerator
    
    # Parse date
    if date_str == 'today':
        report_date = datetime.now().strftime('%Y-%m-%d')
    elif date_str == 'yesterday':
        report_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        report_date = date_str
    
    print(f"\n📊 Activity Report for {report_date}")
    print("=" * 50)
    
    try:
        db = get_database()
        stats = StatsCalculator(db)
        reports = ReportGenerator(db)
        
        # Get daily summary
        daily = stats.get_daily_summary(report_date)
        
        if not daily or daily.get('total_tracked_time', 0) == 0:
            print("  No data available for this date.")
            return
        
        # Format duration
        def format_time(seconds):
            if seconds < 60:
                return f"{seconds}s"
            elif seconds < 3600:
                return f"{seconds // 60}m {seconds % 60}s"
            else:
                hours = seconds // 3600
                mins = (seconds % 3600) // 60
                return f"{hours}h {mins}m"
        
        total = daily.get('total_tracked_time', 0)
        print(f"\n⏱️  Total Tracked Time: {format_time(total)}")
        print(f"📈 Productivity Score: {daily.get('productivity_score', 0):.1f}/100")
        print(f"🔢 Total Sessions: {daily.get('total_sessions', 0)}")
        
        print(f"\n📂 Time by Activity Type:")
        print("-" * 40)
        
        activity_times = [
            ("💻 Productive", daily.get('productive_time', 0)),
            ("📖 Educational", daily.get('educational_time', 0)),
            ("🎬 Entertainment", daily.get('entertainment_time', 0)),
            ("📱 Social Media", daily.get('social_media_time', 0)),
            ("🎮 Gaming", daily.get('gaming_time', 0)),
            ("🛒 Shopping", daily.get('shopping_time', 0)),
            ("📰 News", daily.get('news_time', 0)),
            ("⚪ Neutral", daily.get('neutral_time', 0)),
            ("💤 Idle", daily.get('idle_time', 0)),
        ]
        
        for label, seconds in activity_times:
            if seconds > 0:
                percentage = (seconds / total * 100) if total > 0 else 0
                bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
                print(f"  {label:20} {format_time(seconds):>10} {bar} {percentage:.1f}%")
        
        # Top apps/websites
        top_apps = db.get_top_apps(report_date, limit=5)
        if top_apps:
            print(f"\n🏆 Top Applications:")
            print("-" * 40)
            for i, app in enumerate(top_apps, 1):
                print(f"  {i}. {app['app_name']:30} {format_time(app['total_time'])}")
        
        top_sites = db.get_top_websites(report_date, limit=5)
        if top_sites:
            print(f"\n🌐 Top Websites:")
            print("-" * 40)
            for i, site in enumerate(top_sites, 1):
                print(f"  {i}. {site['website']:30} {format_time(site['total_time'])}")
        
        # NSFW warning
        nsfw_count = daily.get('nsfw_detections', 0)
        if nsfw_count > 0:
            print(f"\n⚠️  NSFW Detections: {nsfw_count}")
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_detection_test():
    """Run a quick detection test."""
    print("\n🧪 Running Detection Test")
    print("=" * 50)
    
    try:
        # Test screenshot capture
        print("\n1. Testing Screenshot Capture...")
        from src.core.screenshot import get_screenshot_capture
        
        capture = get_screenshot_capture()
        screenshot = capture.capture()
        
        if screenshot:
            print(f"   ✅ Screenshot captured: {screenshot.size[0]}x{screenshot.size[1]}")
        else:
            print("   ❌ Screenshot capture failed")
            return
        
        # Test window detection
        print("\n2. Testing Window Detection...")
        from src.core.monitor import get_window_monitor
        
        monitor = get_window_monitor()
        window = monitor.get_active_window()
        
        if window:
            print(f"   ✅ Active Window Detected:")
            print(f"      App: {window.app_name}")
            print(f"      Title: {window.window_title[:50]}...")
            print(f"      Process: {window.process_name}")
            print(f"      Is Browser: {window.is_browser}")
            if window.url:
                print(f"      URL: {window.url}")
        else:
            print("   ❌ Window detection failed")
        
        # Test OCR
        print("\n3. Testing OCR...")
        from src.analyzers.ocr_analyzer import OCRAnalyzer
        
        try:
            ocr = OCRAnalyzer()
            text = ocr.extract_text(screenshot)
            
            if text:
                print(f"   ✅ OCR Extracted {len(text)} characters")
                print(f"      Preview: {text[:100]}...")
            else:
                print("   ⚠️  OCR extracted no text (might be normal)")
        except Exception as e:
            print(f"   ❌ OCR failed: {e}")
        
        # Test content classification
        print("\n4. Testing Content Classification...")
        from src.analyzers.content_classifier import ContentClassifier
        
        try:
            classifier = ContentClassifier()
            result = classifier.classify(screenshot, window)
            
            print(f"   ✅ Classification Result:")
            print(f"      Activity Type: {result.get('activity_type', 'unknown')}")
            print(f"      Content Type: {result.get('content_type', 'unknown')}")
            print(f"      Category: {result.get('content_category', 'unknown')}")
            print(f"      Description: {result.get('content_description', 'N/A')}")
            print(f"      Confidence: {result.get('confidence', 0):.1%}")
            print(f"      Is Productive: {result.get('is_productive', False)}")
            print(f"      Is NSFW: {result.get('is_nsfw', False)}")
        except Exception as e:
            print(f"   ❌ Classification failed: {e}")
        
        # Test database
        print("\n5. Testing Database...")
        from src.storage.database import get_database
        
        try:
            db = get_database()
            counts = db.get_record_count()
            print(f"   ✅ Database connected")
            print(f"      Activities: {counts.get('activities', 0)}")
            print(f"      Size: {db.get_database_size() / 1024:.1f} KB")
        except Exception as e:
            print(f"   ❌ Database failed: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Detection test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_level = args.log_level or config.log_level
    setup_logging(level=log_level, log_dir='logs', use_color=True)
    logger = get_logger(__name__)
    
    # Handle different modes
    if args.version:
        show_version()
        return 0
    
    if args.status:
        show_status()
        return 0
    
    if args.stop:
        logger.info("Stopping daemon...")
        stop_daemon()
        print("✅ Daemon stopped")
        return 0
    
    if args.report:
        generate_report(args.report)
        return 0
    
    if args.test:
        run_detection_test()
        return 0
    
    # Disable ML if requested
    if args.no_ml:
        config.set('detection.use_clip', False)
        config.set('detection.use_nudenet', False)
        logger.info("ML-based detection disabled")
    
    # Start daemon
    try:
        print("""
╔═══════════════════════════════════════════════════════════╗
║          Advanced Content Tracker                         ║
║   "Know exactly what you're watching, reading, and doing" ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info("Starting Content Tracker...")
        
        daemon = get_daemon()
        
        if args.daemon:
            # Run in background (fork)
            logger.info("Starting in daemon mode...")
            daemon.start(blocking=False)
            print("✅ Daemon started in background")
            print("   Use 'python main.py --status' to check status")
            print("   Use 'python main.py --stop' to stop")
        else:
            # Run in foreground
            print("Starting in foreground mode (Ctrl+C to stop)...")
            print("-" * 50)
            daemon.start(blocking=True)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        stop_daemon()
        print("\n✅ Tracker stopped")
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
