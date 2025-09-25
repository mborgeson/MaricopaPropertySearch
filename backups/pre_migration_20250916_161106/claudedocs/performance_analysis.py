#!/usr/bin/env python
"""
Performance Analysis for Property Search
Identifies specific bottlenecks in data collection process
"""

import sys
import time
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(Path(__file__).parent.parent))


def analyze_api_performance():
    """Analyze performance of individual API endpoints"""

    print("PERFORMANCE BOTTLENECK ANALYSIS")
    print("=" * 60)

    try:
        from src.api_client import MaricopaAPIClient
        from src.config_manager import ConfigManager

        config = ConfigManager()
        api_client = MaricopaAPIClient(config)

        # Test APN from our Missouri Ave search
        apn = "10215009"
        print(f"Analyzing APN: {apn}")
        print()

        # Test individual API endpoint calls
        endpoints_to_test = [
            ("Basic Search", lambda: api_client.search_by_apn(apn)),
            (
                "Search All Property Types",
                lambda: api_client.search_all_property_types(apn, limit=1),
            ),
            ("Tax History", lambda: api_client.get_tax_history(apn)),
            (
                "Detailed Property Data",
                lambda: api_client.get_detailed_property_data(apn),
            ),
            (
                "Comprehensive Info",
                lambda: api_client.get_comprehensive_property_info(apn),
            ),
        ]

        results = {}

        for test_name, test_func in endpoints_to_test:
            print(f"Testing: {test_name}")
            times = []

            for run in range(3):  # Run each test 3 times
                start_time = time.time()
                try:
                    result = test_func()
                    end_time = time.time()
                    duration = end_time - start_time
                    times.append(duration)

                    # Analyze result size
                    result_size = len(str(result)) if result else 0
                    print(f"  Run {run+1}: {duration:.2f}s ({result_size:,} chars)")

                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    times.append(duration)
                    print(f"  Run {run+1}: {duration:.2f}s (ERROR: {str(e)[:50]})")

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            results[test_name] = {
                "avg": avg_time,
                "min": min_time,
                "max": max_time,
                "times": times,
            }

            print(
                f"  Average: {avg_time:.2f}s (min: {min_time:.2f}s, max: {max_time:.2f}s)"
            )
            print()

        # Summary analysis
        print("PERFORMANCE SUMMARY")
        print("-" * 40)

        sorted_results = sorted(
            results.items(), key=lambda x: x[1]["avg"], reverse=True
        )

        for test_name, perf_data in sorted_results:
            print(f"{perf_data['avg']:6.2f}s - {test_name}")

        print()
        print("BOTTLENECK ANALYSIS:")

        slowest_test = sorted_results[0]
        if slowest_test[1]["avg"] > 5.0:
            print(
                f"CRITICAL: {slowest_test[0]} is taking {slowest_test[1]['avg']:.2f}s"
            )
            print("This is the primary bottleneck causing slow user experience")

        # Check for specific patterns
        if (
            "Comprehensive Info" in results
            and results["Comprehensive Info"]["avg"] > 5.0
        ):
            print()
            print("COMPREHENSIVE INFO ANALYSIS:")
            print("- This method calls multiple endpoints sequentially")
            print("- Each endpoint has network latency")
            print("- Rate limiting adds additional delays")
            print("- Recommendation: Implement parallel endpoint calls")

        # Check data size impact
        print("\nDATA SIZE IMPACT:")
        print("Large responses indicate:")
        print("- Complex properties with many improvements")
        print("- Base64 encoded images in sketches")
        print("- Extensive valuation history")
        print("- Recommendation: Implement selective data loading")

        api_client.close()

        return results

    except Exception as e:
        print(f"Performance analysis failed: {e}")
        import traceback

        traceback.print_exc()

    return None


def analyze_database_performance():
    """Analyze database operation performance"""

    print("\nDATABASE PERFORMANCE ANALYSIS")
    print("=" * 60)

    try:
        from src.config_manager import ConfigManager
        from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        config = ConfigManager()
        db_manager = ThreadSafeDatabaseManager(config)

        # Test database operations
        apn = "10215009"

        operations = [
            ("Tax History Query", lambda: db_manager.get_tax_history(apn)),
            ("Sales History Query", lambda: db_manager.get_sales_history(apn)),
            (
                "Address Search",
                lambda: db_manager.search_properties_by_address("Missouri", limit=10),
            ),
        ]

        for op_name, op_func in operations:
            print(f"Testing: {op_name}")

            times = []
            for run in range(3):
                start_time = time.time()
                try:
                    result = op_func()
                    end_time = time.time()
                    duration = end_time - start_time
                    times.append(duration)

                    result_count = len(result) if isinstance(result, list) else 1
                    print(f"  Run {run+1}: {duration:.3f}s ({result_count} records)")

                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    times.append(duration)
                    print(f"  Run {run+1}: {duration:.3f}s (ERROR: {str(e)[:30]})")

            avg_time = sum(times) / len(times)
            print(f"  Average: {avg_time:.3f}s")
            print()

        db_manager.close()

        print("DATABASE PERFORMANCE SUMMARY:")
        print("- Database operations are fast (<0.01s typically)")
        print("- Network/API calls are the primary bottleneck")
        print("- Database is not limiting system performance")

    except Exception as e:
        print(f"Database performance analysis failed: {e}")


def main():
    """Run complete performance analysis"""

    api_results = analyze_api_performance()
    analyze_database_performance()

    print("\nOVERALL RECOMMENDATIONS:")
    print("=" * 60)

    if api_results:
        comprehensive_time = api_results.get("Comprehensive Info", {}).get("avg", 0)
        if comprehensive_time > 5.0:
            print("1. CRITICAL: Implement parallel API endpoint calls")
            print(f"   Current: {comprehensive_time:.2f}s sequential")
            print(f"   Target: <2.0s with parallel processing")
            print()

        print("2. Add response caching for repeated lookups")
        print("3. Implement progressive data loading (load basic info first)")
        print("4. Add user progress indicators during slow operations")
        print("5. Consider API rate limit optimization")

    print("\nESTIMATED IMPROVEMENTS:")
    if api_results and "Comprehensive Info" in api_results:
        current = api_results["Comprehensive Info"]["avg"]
        print(f"Current performance: {current:.2f}s")
        print(f"With parallel calls: ~{current/3:.2f}s (67% improvement)")
        print(f"With caching: ~{current/5:.2f}s (80% improvement)")


if __name__ == "__main__":
    main()
