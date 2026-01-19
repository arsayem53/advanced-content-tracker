#!/usr/bin/env python3
"""
Benchmark - Performance testing for Content Tracker components.
Measures speed and resource usage of various detection methods.
"""

import sys
import os
import time
import gc
import statistics
from pathlib import Path
from typing import List, Dict, Callable, Any
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    memory_before: int
    memory_after: int
    memory_delta: int
    success: bool
    error: str = ""


class Benchmark:
    """Benchmark runner for performance testing."""
    
    def __init__(self, iterations: int = 10, warmup: int = 2):
        """
        Initialize benchmark runner.
        
        Args:
            iterations: Number of iterations per test
            warmup: Number of warmup iterations (not counted)
        """
        self.iterations = iterations
        self.warmup = warmup
        self.results: List[BenchmarkResult] = []
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        return 0
    
    def run(self, name: str, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """
        Run a benchmark test.
        
        Args:
            name: Test name
            func: Function to benchmark
            *args: Arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            BenchmarkResult
        """
        print(f"\n⏱️  Benchmarking: {name}")
        print("-" * 40)
        
        times = []
        success = True
        error_msg = ""
        
        # Force garbage collection
        gc.collect()
        memory_before = self.get_memory_usage()
        
        try:
            # Warmup runs
            print(f"   Warmup: {self.warmup} iterations...")
            for _ in range(self.warmup):
                func(*args, **kwargs)
            
            # Timed runs
            print(f"   Running: {self.iterations} iterations...")
            for i in range(self.iterations):
                gc.collect()
                
                start = time.perf_counter()
                func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                
                times.append(elapsed * 1000)  # Convert to ms
                
                if (i + 1) % 5 == 0:
                    print(f"      Progress: {i + 1}/{self.iterations}")
            
        except Exception as e:
            success = False
            error_msg = str(e)
            print(f"   ❌ Error: {e}")
        
        gc.collect()
        memory_after = self.get_memory_usage()
        
        # Calculate statistics
        if times:
            result = BenchmarkResult(
                name=name,
                iterations=len(times),
                total_time=sum(times),
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                std_dev=statistics.stdev(times) if len(times) > 1 else 0,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_delta=memory_after - memory_before,
                success=success,
                error=error_msg
            )
        else:
            result = BenchmarkResult(
                name=name,
                iterations=0,
                total_time=0,
                avg_time=0,
                min_time=0,
                max_time=0,
                std_dev=0,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_delta=memory_after - memory_before,
                success=success,
                error=error_msg
            )
        
        self.results.append(result)
        self._print_result(result)
        
        return result
    
    def _print_result(self, result: BenchmarkResult):
        """Print a single result."""
        if result.success:
            print(f"   ✅ Completed")
            print(f"      Avg: {result.avg_time:.2f} ms")
            print(f"      Min: {result.min_time:.2f} ms")
            print(f"      Max: {result.max_time:.2f} ms")
            print(f"      Std Dev: {result.std_dev:.2f} ms")
            if HAS_PSUTIL:
                print(f"      Memory Delta: {result.memory_delta / 1024 / 1024:.2f} MB")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    def print_summary(self):
        """Print summary of all benchmark results."""
        print("\n" + "=" * 60)
        print("                 BENCHMARK SUMMARY")
        print("=" * 60)
        
        print(f"\n{'Test Name':<30} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'Status':<10}")
        print("-" * 76)
        
        for result in self.results:
            status = "✅ Pass" if result.success else "❌ Fail"
            print(f"{result.name:<30} {result.avg_time:<12.2f} {result.min_time:<12.2f} {result.max_time:<12.2f} {status:<10}")
        
        # Performance grades
        print("\n📊 Performance Analysis:")
        print("-" * 40)
        
        for result in self.results:
            if result.success and result.avg_time > 0:
                if result.avg_time < 50:
                    grade = "🟢 Excellent"
                elif result.avg_time < 100:
                    grade = "🟡 Good"
                elif result.avg_time < 500:
                    grade = "🟠 Acceptable"
                else:
                    grade = "🔴 Slow"
                print(f"   {result.name}: {grade} ({result.avg_time:.0f}ms)")
        
        # Memory usage
        if HAS_PSUTIL:
            print("\n💾 Memory Usage:")
            print("-" * 40)
            total_memory = sum(r.memory_delta for r in self.results)
            print(f"   Total memory delta: {total_memory / 1024 / 1024:.2f} MB")
        
        print("\n" + "=" * 60 + "\n")


def benchmark_screenshot():
    """Benchmark screenshot capture."""
    from src.core.screenshot import get_screenshot_capture
    
    capture = get_screenshot_capture()
    
    def capture_screenshot():
        img = capture.capture()
        if img is None:
            raise Exception("Screenshot capture failed")
        return img
    
    return capture_screenshot


def benchmark_window_monitor():
    """Benchmark window monitoring."""
    from src.core.monitor import get_window_monitor
    
    monitor = get_window_monitor()
    
    def get_window():
        window = monitor.get_active_window()
        return window
    
    return get_window


def benchmark_ocr(screenshot):
    """Benchmark OCR extraction."""
    from src.analyzers.ocr_analyzer import OCRAnalyzer
    
    ocr = OCRAnalyzer()
    
    def extract_text():
        return ocr.extract_text(screenshot)
    
    return extract_text


def benchmark_image_analysis(screenshot):
    """Benchmark image analysis."""
    from src.analyzers.image_analyzer import ImageAnalyzer
    
    analyzer = ImageAnalyzer()
    
    def analyze_image():
        colors = analyzer.analyze_colors(screenshot)
        layout = analyzer.analyze_layout(screenshot)
        return colors, layout
    
    return analyze_image


def benchmark_app_detector():
    """Benchmark app detection."""
    from src.detectors.app_detector import AppDetector
    
    detector = AppDetector()
    test_cases = [
        ("code", "Code", "main.py - VSCode"),
        ("firefox", "Firefox", "GitHub - Mozilla Firefox"),
        ("vlc", "VLC", "Movie.mp4 - VLC"),
        ("gnome-terminal", "Terminal", "~/projects"),
    ]
    
    def detect_apps():
        for process, wm_class, title in test_cases:
            detector.detect(process, wm_class, title)
    
    return detect_apps


def benchmark_website_detector():
    """Benchmark website detection."""
    from src.detectors.website_detector import WebsiteDetector
    
    detector = WebsiteDetector()
    test_urls = [
        "https://github.com/user/repo",
        "https://www.youtube.com/watch?v=abc123",
        "https://twitter.com/user/status/123",
        "https://stackoverflow.com/questions/123456",
        "https://www.amazon.com/dp/B01234567",
    ]
    
    def detect_websites():
        for url in test_urls:
            detector.detect(url)
    
    return detect_websites


def benchmark_video_detector():
    """Benchmark video content detection."""
    from src.detectors.video_detector import VideoDetector
    
    detector = VideoDetector()
    test_titles = [
        "Python Tutorial for Beginners - Full Course 2024",
        "Minecraft Let's Play Episode 25 - Building a Castle",
        "Official Music Video - Popular Artist - Hit Song",
        "Attack on Titan Episode 1 [English Subbed]",
        "🔴 LIVE: 24/7 Lofi Hip Hop Radio - Beats to Study/Relax to",
    ]
    
    def detect_videos():
        for title in test_titles:
            detector.detect(title)
    
    return detect_videos


def benchmark_activity_detector():
    """Benchmark activity detection."""
    from src.detectors.activity_detector import ActivityDetector
    
    detector = ActivityDetector()
    
    def detect_activity():
        detector.detect(
            app_name="VS Code",
            process_name="code",
            window_title="main.py - project - Visual Studio Code",
            url="",
            wm_class="Code",
            is_browser=False
        )
        detector.detect(
            app_name="Firefox",
            process_name="firefox",
            window_title="GitHub: Let's build - Mozilla Firefox",
            url="https://github.com",
            wm_class="Firefox",
            is_browser=True
        )
    
    return detect_activity


def benchmark_content_classifier(screenshot, window_info):
    """Benchmark full content classification."""
    from src.analyzers.content_classifier import ContentClassifier
    
    classifier = ContentClassifier()
    
    def classify():
        return classifier.classify(screenshot, window_info)
    
    return classify


def benchmark_database():
    """Benchmark database operations."""
    from src.storage.database import get_database
    from src.storage.models import Activity
    from datetime import datetime
    
    db = get_database()
    
    def db_operations():
        # Insert
        activity = Activity(
            timestamp=datetime.now(),
            app_name="Benchmark Test",
            window_title="Test Window",
            activity_type="productive",
            content_type="test",
            duration=30
        )
        activity_id = db.insert_activity(activity)
        
        # Query
        db.get_recent_activities(hours=1)
        db.get_time_by_category()
    
    return db_operations


def main():
    """Run all benchmarks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Content Tracker components")
    parser.add_argument('--iterations', '-i', type=int, default=10, help='Iterations per test')
    parser.add_argument('--warmup', '-w', type=int, default=2, help='Warmup iterations')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick mode (fewer iterations)')
    parser.add_argument('--component', '-c', type=str, help='Benchmark specific component')
    args = parser.parse_args()
    
    if args.quick:
        args.iterations = 3
        args.warmup = 1
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║         Content Tracker - Performance Benchmark           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"Configuration:")
    print(f"   Iterations: {args.iterations}")
    print(f"   Warmup: {args.warmup}")
    print(f"   Python: {sys.version.split()[0]}")
    if HAS_PSUTIL:
        print(f"   Memory tracking: Enabled")
    else:
        print(f"   Memory tracking: Disabled (install psutil)")
    
    benchmark = Benchmark(iterations=args.iterations, warmup=args.warmup)
    
    # Get screenshot for image-based benchmarks
    print("\n📷 Capturing reference screenshot...")
    from src.core.screenshot import get_screenshot_capture
    capture = get_screenshot_capture()
    screenshot = capture.capture()
    
    if screenshot is None:
        print("❌ Failed to capture screenshot. Some benchmarks will be skipped.")
    else:
        print(f"   Screenshot: {screenshot.size[0]}x{screenshot.size[1]}")
    
    # Get window info
    from src.core.monitor import get_window_monitor
    monitor = get_window_monitor()
    window_info = monitor.get_active_window()
    
    # Run benchmarks
    components = [
        ('screenshot', lambda: benchmark.run("Screenshot Capture", benchmark_screenshot())),
        ('window', lambda: benchmark.run("Window Monitor", benchmark_window_monitor())),
        ('app', lambda: benchmark.run("App Detector", benchmark_app_detector())),
        ('website', lambda: benchmark.run("Website Detector", benchmark_website_detector())),
        ('video', lambda: benchmark.run("Video Detector", benchmark_video_detector())),
        ('activity', lambda: benchmark.run("Activity Detector", benchmark_activity_detector())),
        ('database', lambda: benchmark.run("Database Operations", benchmark_database())),
    ]
    
    # Add image-based benchmarks if screenshot available
    if screenshot:
        components.extend([
            ('ocr', lambda: benchmark.run("OCR Extraction", benchmark_ocr(screenshot))),
            ('image', lambda: benchmark.run("Image Analysis", benchmark_image_analysis(screenshot))),
            ('classifier', lambda: benchmark.run("Content Classifier", benchmark_content_classifier(screenshot, window_info))),
        ])
    
    # Run selected or all benchmarks
    if args.component:
        for name, func in components:
            if name == args.component:
                func()
                break
        else:
            print(f"❌ Unknown component: {args.component}")
            print(f"   Available: {', '.join(name for name, _ in components)}")
            return 1
    else:
        for name, func in components:
            try:
                func()
            except Exception as e:
                print(f"❌ Benchmark '{name}' failed: {e}")
    
    # Print summary
    benchmark.print_summary()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
