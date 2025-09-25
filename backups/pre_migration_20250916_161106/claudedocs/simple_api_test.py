#!/usr/bin/env python
"""
Simple API Test for Missouri Ave Property Search
Direct test without Unicode issues
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Simple test of the API functionality"""

    print("SIMPLE API TEST FOR 10000 W MISSOURI AVE")
    print("=" * 50)

    try:
        from src.api_client import MaricopaAPIClient
        from src.config_manager import ConfigManager

        config = ConfigManager()
        api_client = MaricopaAPIClient(config)

        # Test 1: Search
        print("1. SEARCHING FOR PROPERTY...")
        search_results = api_client.search_by_address("10000 W Missouri Ave", limit=10)

        print(f"Search Results: {len(search_results)} properties found")

        if search_results:
            first_result = search_results[0]
            print(f"First Result APN: {first_result.get('apn')}")
            print(f"Address: {first_result.get('property_address')}")
            print(f"Owner: {first_result.get('owner_name')}")
            print(f"Property Type: {first_result.get('property_type')}")

            # Test 2: Get detailed info
            apn = first_result.get("apn")
            print(f"\n2. GETTING DETAILED INFO FOR APN: {apn}")

            start_time = time.time()
            detailed_info = api_client.get_comprehensive_property_info(apn)
            detail_time = time.time() - start_time

            print(f"Detailed info retrieved in {detail_time:.2f} seconds")

            if detailed_info:
                print("Key Property Details:")
                print(f"  Year Built: {detailed_info.get('year_built', 'N/A')}")
                print(
                    f"  Living Area: {detailed_info.get('living_area_sqft', 'N/A')} sqft"
                )
                print(f"  Lot Size: {detailed_info.get('lot_size_sqft', 'N/A')} sqft")
                print(
                    f"  Assessed Value: ${detailed_info.get('latest_assessed_value', 0):,}"
                    if detailed_info.get("latest_assessed_value")
                    else "  Assessed Value: N/A"
                )
                print(
                    f"  Property Use: {detailed_info.get('property_use_description', 'N/A')}"
                )
                print(
                    f"  Improvements: {detailed_info.get('improvements_count', 'N/A')}"
                )

            # Test 3: Tax history
            print(f"\n3. GETTING TAX HISTORY FOR APN: {apn}")

            start_time = time.time()
            tax_history = api_client.get_tax_history(apn)
            tax_time = time.time() - start_time

            print(f"Tax history retrieved in {tax_time:.2f} seconds")
            print(f"Tax records found: {len(tax_history)}")

            if tax_history and len(tax_history) > 0:
                print("Recent tax records:")
                for i, record in enumerate(tax_history[:3]):
                    year = record.get("TaxYear", "N/A")
                    full_value = record.get("FullCashValue", "N/A")
                    limited_value = record.get("LimitedPropertyValue", "N/A")
                    print(
                        f"  {year}: Full=${full_value:,} Limited=${limited_value:,}"
                        if isinstance(full_value, (int, float))
                        else f"  {year}: {full_value} | {limited_value}"
                    )

            # Test 4: Performance analysis
            print(f"\n4. PERFORMANCE ANALYSIS")
            print(f"Detailed property lookup: {detail_time:.2f}s")
            print(f"Tax history lookup: {tax_time:.2f}s")
            print(f"Total API time: {detail_time + tax_time:.2f}s")

            if detail_time > 5:
                print("WARNING: Detailed property lookup is slow (>5s)")
                print(
                    "This suggests API endpoint delays in get_comprehensive_property_info"
                )

        else:
            print("ERROR: No search results found!")

        # Test 5: Alternative searches
        print("\n5. TESTING ALTERNATIVE SEARCH PATTERNS")
        alternatives = ["Missouri Ave", "10000 Missouri", "Missouri Avenue"]

        for search_term in alternatives:
            start_time = time.time()
            alt_results = api_client.search_by_address(search_term, limit=3)
            alt_time = time.time() - start_time
            print(f"  '{search_term}': {len(alt_results)} results in {alt_time:.2f}s")

        # Cleanup
        api_client.close()

        print("\nTEST COMPLETED SUCCESSFULLY")
        return True

    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback

        traceback.print_exc()

    return False


if __name__ == "__main__":
    success = main()
    print("\nRESULT:", "PASS" if success else "FAIL")
