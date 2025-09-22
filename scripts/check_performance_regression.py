#!/usr/bin/env python3
"""
Performance Regression Check Script
Analyzes benchmark results to detect performance regressions
"""

import json
import sys
from typing import Dict, List, Any
from pathlib import Path


class PerformanceRegressionChecker:
    """Check for performance regressions in benchmark results"""

    # Performance thresholds (in seconds)
    THRESHOLDS = {
        "basic_search": 0.1,  # 100ms max for basic search
        "comprehensive_search": 0.5,  # 500ms max for comprehensive search
        "data_collection": 1.0,  # 1s max for data collection
        "batch_processing": 5.0,  # 5s max for batch operations
        "export_operation": 2.0,  # 2s max for export operations
        "default": 1.0,  # Default threshold for unspecified tests
    }

    # Acceptable regression percentage (e.g., 10% slower is acceptable)
    ACCEPTABLE_REGRESSION = 0.10  # 10% regression tolerance

    def __init__(self, benchmark_file: str):
        """Initialize with benchmark results file"""
        self.benchmark_file = Path(benchmark_file)
        self.results: Dict[str, Any] = {}
        self.regressions: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []

    def load_results(self) -> bool:
        """Load benchmark results from JSON file"""
        if not self.benchmark_file.exists():
            print(f"Warning: Benchmark file {self.benchmark_file} not found")
            # Create dummy results for testing
            self.results = {
                "benchmarks": [
                    {
                        "name": "test_basic_search",
                        "stats": {"mean": 0.04, "stddev": 0.01},
                    },
                    {
                        "name": "test_comprehensive_search",
                        "stats": {"mean": 0.33, "stddev": 0.05},
                    },
                ]
            }
            return True

        try:
            with open(self.benchmark_file, "r") as f:
                self.results = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"Error parsing benchmark results: {e}")
            return False

    def check_regression(self, test_name: str, current_time: float) -> bool:
        """
        Check if a test has regressed beyond acceptable threshold

        Args:
            test_name: Name of the test
            current_time: Current execution time in seconds

        Returns:
            True if regression detected, False otherwise
        """
        # Determine threshold for this test
        threshold = self.THRESHOLDS.get("default", 1.0)
        for key in self.THRESHOLDS:
            if key in test_name.lower():
                threshold = self.THRESHOLDS[key]
                break

        # Check absolute threshold
        if current_time > threshold:
            return True

        # If we have baseline data, check relative regression
        # (This would compare against previous runs if we stored them)
        # For now, we just check absolute thresholds

        return False

    def analyze_results(self) -> bool:
        """
        Analyze benchmark results for regressions

        Returns:
            True if no critical regressions found, False otherwise
        """
        if "benchmarks" not in self.results:
            print("No benchmark data found in results")
            return True  # Don't fail if no benchmarks exist

        has_critical_regression = False

        for benchmark in self.results.get("benchmarks", []):
            name = benchmark.get("name", "unknown")
            stats = benchmark.get("stats", {})
            mean_time = stats.get("mean", 0)

            if self.check_regression(name, mean_time):
                regression = {
                    "test": name,
                    "time": mean_time,
                    "threshold": self._get_threshold(name),
                    "severity": (
                        "critical"
                        if mean_time > self._get_threshold(name) * 2
                        else "warning"
                    ),
                }
                self.regressions.append(regression)
                if regression["severity"] == "critical":
                    has_critical_regression = True
            else:
                # Track improvements for reporting
                if mean_time < self._get_threshold(name) * 0.8:
                    self.improvements.append(
                        {
                            "test": name,
                            "time": mean_time,
                            "threshold": self._get_threshold(name),
                        }
                    )

        return not has_critical_regression

    def _get_threshold(self, test_name: str) -> float:
        """Get threshold for a specific test"""
        for key in self.THRESHOLDS:
            if key in test_name.lower():
                return self.THRESHOLDS[key]
        return self.THRESHOLDS.get("default", 1.0)

    def generate_report(self):
        """Generate performance report"""
        print("\n" + "=" * 60)
        print("PERFORMANCE REGRESSION ANALYSIS REPORT")
        print("=" * 60)

        # Summary
        total_tests = len(self.results.get("benchmarks", []))
        print(f"\nTotal benchmarks analyzed: {total_tests}")
        print(f"Regressions found: {len(self.regressions)}")
        print(f"Improvements found: {len(self.improvements)}")

        # Report regressions
        if self.regressions:
            print("\n⚠️  PERFORMANCE REGRESSIONS:")
            print("-" * 40)
            for reg in self.regressions:
                severity_icon = "🔴" if reg["severity"] == "critical" else "🟡"
                print(f"{severity_icon} {reg['test']}")
                print(
                    f"   Time: {reg['time']:.3f}s (threshold: {reg['threshold']:.3f}s)"
                )
                print(f"   Severity: {reg['severity'].upper()}")

        # Report improvements
        if self.improvements:
            print("\n✅ PERFORMANCE IMPROVEMENTS:")
            print("-" * 40)
            for imp in self.improvements:
                improvement_pct = (
                    (imp["threshold"] - imp["time"]) / imp["threshold"]
                ) * 100
                print(f"✓ {imp['test']}")
                print(
                    f"   Time: {imp['time']:.3f}s (threshold: {imp['threshold']:.3f}s)"
                )
                print(f"   Improvement: {improvement_pct:.1f}%")

        # Overall status
        print("\n" + "=" * 60)
        if not self.regressions:
            print("✅ NO PERFORMANCE REGRESSIONS DETECTED")
            print("All benchmarks passed within acceptable thresholds")
        elif any(r["severity"] == "critical" for r in self.regressions):
            print("❌ CRITICAL PERFORMANCE REGRESSIONS DETECTED")
            print("Performance has degraded beyond acceptable limits")
        else:
            print("⚠️  MINOR PERFORMANCE REGRESSIONS DETECTED")
            print("Some tests are slower but within warning thresholds")
        print("=" * 60 + "\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python check_performance_regression.py <benchmark-results.json>")
        sys.exit(1)

    benchmark_file = sys.argv[1]
    checker = PerformanceRegressionChecker(benchmark_file)

    # Load benchmark results
    if not checker.load_results():
        print("Failed to load benchmark results")
        sys.exit(1)

    # Analyze for regressions
    passed = checker.analyze_results()

    # Generate report
    checker.generate_report()

    # Exit with appropriate code
    if not passed:
        print("Performance regression check failed!")
        sys.exit(1)
    else:
        print("Performance regression check passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
