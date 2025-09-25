#!/usr/bin/env python3
"""
Test API functionality with real APNs found through owner search
This test will first find valid APNs through owner search, then test all API methods with them
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
    def find_valid_apns(client, max_apns=5):
    """Find valid APNs by searching for common owner names"""
    logger.info("Finding valid APNs through owner search...")

    valid_apns = []

    # Search for different types of owners that typically have many properties
    owner_searches = [
        "SMITH",
        "JOHNSON",
        "CITY OF PHOENIX",
        "COUNTY OF MARICOPA",
        "ARIZONA STATE",
    ]

    for owner in owner_searches:
        if len(valid_apns) >= max_apns:
            break

try:
            logger.info(f"Searching for properties owned by: {owner}")
            results = client.search_by_owner(owner, limit=10)

            if results:
                for result in results:
                    if len(valid_apns) >= max_apns:
                        break

                    apn = result.get("apn")
                    if apn and apn not in valid_apns:
                        valid_apns.append(apn)
                        logger.info(
                            f"Found valid APN: {apn} (Owner: {result.get('owner_name', 'Unknown')})"
                        )

                        # Add a delay between requests
                        time.sleep(0.2)

except Exception as e:
            logger.error(f"Error searching for owner {owner}: {e}")
            continue

    logger.info(f"Found {len(valid_apns)} valid APNs: {valid_apns}")
    return valid_apns
    def test_apn_search_detailed(client, apns):
    """Test APN search with detailed analysis"""
    logger.info("Testing APN search with real APNs...")

    results = []

    for apn in apns:
        logger.info(f"Testing APN search for: {apn}")

        test_result = {
            "apn": apn,
            "search_result": None,
            "property_details": None,
            "comprehensive_info": None,
            "errors": [],
        }

try:
            # Test basic search
            start_time = time.time()
            search_result = client.search_by_apn(apn)
            search_time = time.time() - start_time

            test_result["search_result"] = search_result
            test_result["search_time"] = search_time

            if search_result:
                logger.info(f"✅ APN search successful for {apn}")

                # Test property details
try:
                    start_time = time.time()
                    details = client.get_property_details(apn)
                    details_time = time.time() - start_time

                    test_result["property_details"] = details
                    test_result["details_time"] = details_time

                    if details:
                        logger.info(f"✅ Property details retrieved for {apn}")
                    else:
                        logger.warning(f"⚠️  No property details for {apn}")

except Exception as e:
                    error_msg = f"Property details error for {apn}: {e}"
                    logger.error(f"❌ {error_msg}")
                    test_result["errors"].append(error_msg)

                # Test comprehensive info
try:
                    start_time = time.time()
                    comp_info = client.get_comprehensive_property_info(apn)
                    comp_time = time.time() - start_time

                    test_result["comprehensive_info"] = comp_info
                    test_result["comprehensive_time"] = comp_time

                    if comp_info:
                        logger.info(f"✅ Comprehensive info retrieved for {apn}")

                        # Check what data fields are available
                        available_fields = [
                            k for k, v in comp_info.items() if v is not None and v != ""
                        ]
                        test_result["available_fields"] = available_fields
                        logger.info(
                            f"   Available fields: {len(available_fields)} fields"
                        )

                    else:
                        logger.warning(f"⚠️  No comprehensive info for {apn}")

except Exception as e:
                    error_msg = f"Comprehensive info error for {apn}: {e}"
                    logger.error(f"❌ {error_msg}")
                    test_result["errors"].append(error_msg)

            else:
                logger.warning(f"⚠️  No search results for {apn}")

except Exception as e:
            error_msg = f"APN search error for {apn}: {e}"
            logger.error(f"❌ {error_msg}")
            test_result["errors"].append(error_msg)

        results.append(test_result)

        # Rate limiting delay
        time.sleep(0.3)

    return results
    def test_tax_and_sales_detailed(client, apns):
    """Test tax and sales history with real APNs"""
    logger.info("Testing tax and sales history with real APNs...")

    results = []

    for apn in apns:
        logger.info(f"Testing tax/sales for: {apn}")

        test_result = {
            "apn": apn,
            "tax_history": None,
            "sales_history": None,
            "tax_info": None,
            "documents": None,
            "errors": [],
        }

        # Test tax history
try:
            start_time = time.time()
            tax_history = client.get_tax_history(apn, years=5)
            tax_time = time.time() - start_time

            test_result["tax_history"] = tax_history
            test_result["tax_time"] = tax_time

            if tax_history:
                logger.info(
                    f"✅ Tax history retrieved for {apn}: {len(tax_history)} records"
                )
            else:
                logger.warning(f"⚠️  No tax history for {apn}")

except Exception as e:
            error_msg = f"Tax history error for {apn}: {e}"
            logger.error(f"❌ {error_msg}")
            test_result["errors"].append(error_msg)

        # Test comprehensive tax information
try:
            start_time = time.time()
            tax_info = client.get_tax_information(apn)
            tax_info_time = time.time() - start_time

            test_result["tax_info"] = tax_info
            test_result["tax_info_time"] = tax_info_time

            if tax_info:
                data_sources = tax_info.get("data_sources", [])
                logger.info(
                    f"✅ Tax information retrieved for {apn} from sources: {data_sources}"
                )
            else:
                logger.warning(f"⚠️  No tax information for {apn}")

except Exception as e:
            error_msg = f"Tax information error for {apn}: {e}"
            logger.error(f"❌ {error_msg}")
            test_result["errors"].append(error_msg)

        # Test sales history
try:
            start_time = time.time()
            sales_history = client.get_sales_history(apn, years=10)
            sales_time = time.time() - start_time

            test_result["sales_history"] = sales_history
            test_result["sales_time"] = sales_time

            if sales_history:
                logger.info(
                    f"✅ Sales history retrieved for {apn}: {len(sales_history)} records"
                )
            else:
                logger.warning(f"⚠️  No sales history for {apn}")

except Exception as e:
            error_msg = f"Sales history error for {apn}: {e}"
            logger.error(f"❌ {error_msg}")
            test_result["errors"].append(error_msg)

        # Test property documents
try:
            start_time = time.time()
            documents = client.get_property_documents(apn)
            docs_time = time.time() - start_time

            test_result["documents"] = documents
            test_result["docs_time"] = docs_time

            if documents:
                logger.info(
                    f"✅ Documents retrieved for {apn}: {len(documents)} documents"
                )
            else:
                logger.warning(f"⚠️  No documents for {apn}")

except Exception as e:
            error_msg = f"Documents error for {apn}: {e}"
            logger.error(f"❌ {error_msg}")
            test_result["errors"].append(error_msg)

        results.append(test_result)

        # Rate limiting delay
        time.sleep(0.5)

    return results
    def test_endpoint_discovery(client):
    """Test various endpoint discovery methods"""
    logger.info("Testing endpoint discovery and detailed data methods...")

    results = {
        "all_property_types": None,
        "detailed_property_data": None,
        "api_status": None,
        "errors": [],
    }

    # Test search all property types
try:
        logger.info("Testing search all property types...")
        all_types = client.search_all_property_types("PHOENIX", limit=5)
        results["all_property_types"] = all_types

        total_results = sum(len(results) for results in all_types.values())
        logger.info(
            f"✅ All property types search: {total_results} total results across all categories"
        )

        for category, properties in all_types.items():
            if properties:
                logger.info(f"   {category}: {len(properties)} results")

except Exception as e:
        error_msg = f"All property types search error: {e}"
        logger.error(f"❌ {error_msg}")
        results["errors"].append(error_msg)

    # Test API status
try:
        logger.info("Testing API status...")
        api_status = client.get_api_status()
        results["api_status"] = api_status

        if api_status:
            logger.info(
                f"✅ API status retrieved: {api_status.get('status', 'Unknown')}"
            )
        else:
            logger.warning("⚠️  No API status returned")

except Exception as e:
        error_msg = f"API status error: {e}"
        logger.error(f"❌ {error_msg}")
        results["errors"].append(error_msg)

    return results
    def generate_detailed_report(
    apn_results, tax_sales_results, endpoint_results, test_duration
):
    """Generate a detailed report of all test results"""

    report_lines = [
        "=" * 80,
        "MARICOPA API - DETAILED FUNCTIONALITY TEST REPORT",
        "=" * 80,
        f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duration: {test_duration:.2f} seconds",
        "",
        "SUMMARY:",
        "-" * 40,
    ]

    # APN Search Summary
    total_apns = len(apn_results)
    successful_searches = sum(1 for r in apn_results if r["search_result"] is not None)
    successful_details = sum(
        1 for r in apn_results if r["property_details"] is not None
    )
    successful_comprehensive = sum(
        1 for r in apn_results if r["comprehensive_info"] is not None
    )

    report_lines.extend(
        [
            f"APN Search Tests: {successful_searches}/{total_apns} successful ({(successful_searches/total_apns*100):.1f}%)",
            f"Property Details: {successful_details}/{total_apns} successful ({(successful_details/total_apns*100):.1f}%)",
            f"Comprehensive Info: {successful_comprehensive}/{total_apns} successful ({(successful_comprehensive/total_apns*100):.1f}%)",
            "",
        ]
    )

    # Tax & Sales Summary
    successful_tax = sum(
        1 for r in tax_sales_results if r["tax_history"] and len(r["tax_history"]) > 0
    )
    successful_tax_info = sum(1 for r in tax_sales_results if r["tax_info"] is not None)
    successful_sales = sum(
        1
        for r in tax_sales_results
        if r["sales_history"] and len(r["sales_history"]) > 0
    )
    successful_docs = sum(
        1 for r in tax_sales_results if r["documents"] and len(r["documents"]) > 0
    )

    report_lines.extend(
        [
            f"Tax History: {successful_tax}/{total_apns} successful ({(successful_tax/total_apns*100):.1f}%)",
            f"Tax Information: {successful_tax_info}/{total_apns} successful ({(successful_tax_info/total_apns*100):.1f}%)",
            f"Sales History: {successful_sales}/{total_apns} successful ({(successful_sales/total_apns*100):.1f}%)",
            f"Property Documents: {successful_docs}/{total_apns} successful ({(successful_docs/total_apns*100):.1f}%)",
            "",
        ]
    )

    # Detailed APN Results
    report_lines.extend(["DETAILED APN TEST RESULTS:", "-" * 40, ""])

    for result in apn_results:
        apn = result["apn"]
        report_lines.append(f"APN: {apn}")

        # Search results
        if result["search_result"]:
            search_data = result["search_result"]
            report_lines.append(
                f"  ✅ Search: SUCCESS ({result.get('search_time', 0):.3f}s)"
            )
            report_lines.append(f"     Owner: {search_data.get('owner_name', 'N/A')}")
            report_lines.append(
                f"     Address: {search_data.get('property_address', 'N/A')}"
            )
        else:
            report_lines.append(f"  ❌ Search: NO RESULTS")

        # Property details
        if result["property_details"]:
            report_lines.append(
                f"  ✅ Details: SUCCESS ({result.get('details_time', 0):.3f}s)"
            )
        else:
            report_lines.append(f"  ❌ Details: NO DATA")

        # Comprehensive info
        if result["comprehensive_info"]:
            fields = result.get("available_fields", [])
            report_lines.append(
                f"  ✅ Comprehensive: SUCCESS ({result.get('comprehensive_time', 0):.3f}s)"
            )
            report_lines.append(f"     Fields: {len(fields)} available")
        else:
            report_lines.append(f"  ❌ Comprehensive: NO DATA")

        # Errors
        if result["errors"]:
            for error in result["errors"]:
                report_lines.append(f"  🚨 Error: {error}")

        report_lines.append("")

    # Tax and Sales Results
    report_lines.extend(["TAX AND SALES HISTORY RESULTS:", "-" * 40, ""])

    for result in tax_sales_results:
        apn = result["apn"]
        report_lines.append(f"APN: {apn}")

        # Tax history
        if result["tax_history"]:
            count = len(result["tax_history"])
            report_lines.append(
                f"  ✅ Tax History: {count} records ({result.get('tax_time', 0):.3f}s)"
            )
        else:
            report_lines.append(f"  ❌ Tax History: NO DATA")

        # Tax information
        if result["tax_info"]:
            sources = result["tax_info"].get("data_sources", [])
            report_lines.append(
                f"  ✅ Tax Info: Sources {sources} ({result.get('tax_info_time', 0):.3f}s)"
            )
        else:
            report_lines.append(f"  ❌ Tax Info: NO DATA")

        # Sales history
        if result["sales_history"]:
            count = len(result["sales_history"])
            report_lines.append(
                f"  ✅ Sales History: {count} records ({result.get('sales_time', 0):.3f}s)"
            )
        else:
            report_lines.append(f"  ❌ Sales History: NO DATA")

        # Documents
        if result["documents"]:
            count = len(result["documents"])
            report_lines.append(
                f"  ✅ Documents: {count} records ({result.get('docs_time', 0):.3f}s)"
            )
        else:
            report_lines.append(f"  ❌ Documents: NO DATA")

        # Errors
        if result["errors"]:
            for error in result["errors"]:
                report_lines.append(f"  🚨 Error: {error}")

        report_lines.append("")

    # Endpoint Discovery Results
    report_lines.extend(["ENDPOINT DISCOVERY RESULTS:", "-" * 40, ""])

    if endpoint_results["all_property_types"]:
        all_types = endpoint_results["all_property_types"]
        total = sum(len(results) for results in all_types.values())
        report_lines.append(f"✅ All Property Types Search: {total} total results")

        for category, properties in all_types.items():
            count = len(properties)
            if count > 0:
                report_lines.append(f"   {category}: {count} properties")
    else:
        report_lines.append("❌ All Property Types Search: FAILED")

    if endpoint_results["api_status"]:
        status = endpoint_results["api_status"]
        report_lines.append(f"✅ API Status: {status.get('status', 'Unknown')}")
        report_lines.append(f"   Version: {status.get('version', 'Unknown')}")
        report_lines.append(f"   Endpoints: {status.get('endpoints', [])}")
    else:
        report_lines.append("❌ API Status: FAILED")

    if endpoint_results["errors"]:
        report_lines.append("")
        report_lines.append("ENDPOINT ERRORS:")
        for error in endpoint_results["errors"]:
            report_lines.append(f"  🚨 {error}")

    # Overall Assessment
    report_lines.extend(["", "OVERALL ASSESSMENT:", "-" * 30, ""])

    # Working features
    working_features = []
    if successful_searches > 0:
        working_features.append("APN Search")
    if successful_details > 0:
        working_features.append("Property Details")
    if successful_comprehensive > 0:
        working_features.append("Comprehensive Property Info")
    if successful_tax > 0:
        working_features.append("Tax History")
    if successful_tax_info > 0:
        working_features.append("Tax Information")
    if successful_sales > 0:
        working_features.append("Sales History")
    if successful_docs > 0:
        working_features.append("Property Documents")
    if endpoint_results["all_property_types"]:
        working_features.append("All Property Types Search")
    if endpoint_results["api_status"]:
        working_features.append("API Status")

    if working_features:
        report_lines.append("✅ WORKING FEATURES:")
        for feature in working_features:
            report_lines.append(f"   • {feature}")
        report_lines.append("")

    # Broken features
    broken_features = []
    if successful_searches == 0:
        broken_features.append("APN Search")
    if successful_details == 0:
        broken_features.append("Property Details")
    if successful_comprehensive == 0:
        broken_features.append("Comprehensive Property Info")
    if successful_tax == 0:
        broken_features.append("Tax History")
    if successful_tax_info == 0:
        broken_features.append("Tax Information")
    if successful_sales == 0:
        broken_features.append("Sales History")
    if successful_docs == 0:
        broken_features.append("Property Documents")
    if not endpoint_results["all_property_types"]:
        broken_features.append("All Property Types Search")
    if not endpoint_results["api_status"]:
        broken_features.append("API Status")

    if broken_features:
        report_lines.append("❌ BROKEN/MISSING FEATURES:")
        for feature in broken_features:
            report_lines.append(f"   • {feature}")
        report_lines.append("")

    # Issues found
    all_errors = []
    for result in apn_results + tax_sales_results:
        all_errors.extend(result.get("errors", []))
    all_errors.extend(endpoint_results.get("errors", []))

    if all_errors:
        report_lines.append("🚨 ISSUES FOUND:")
        for error in set(all_errors):  # Remove duplicates
            report_lines.append(f"   • {error}")
        report_lines.append("")

    # Recommendations
    report_lines.extend(["RECOMMENDATIONS:", "-" * 20, ""])

    if successful_searches == 0:
        report_lines.extend(
            [
                "🔧 CRITICAL: APN search not working with real APNs",
                "   • Verify API endpoint URLs are correct",
                "   • Check APN format requirements",
                "   • Test with different APN formats",
                "",
            ]
        )

    if successful_tax == 0 and successful_sales == 0:
        report_lines.extend(
            [
                "⚠️  WARNING: Tax and sales data unavailable",
                "   • This may be due to missing Playwright dependency",
                "   • Consider implementing API-based alternatives",
                "   • Add fallback data sources",
                "",
            ]
        )

    if working_features:
        report_lines.extend(
            [
                "✅ RECOMMENDATIONS:",
                "   • Focus on working features for production use",
                "   • Implement proper error handling for broken features",
                "   • Add retry logic for intermittent failures",
                "   • Consider caching successful API responses",
                "",
            ]
        )

    report_lines.extend(["=" * 80, "END OF DETAILED REPORT", "=" * 80])

    return "\n".join(report_lines)
    def main():
    """Main test execution with real APNs"""
        print("Starting Maricopa API Detailed Test with Real APNs...")
        print("=" * 60)

    start_time = time.time()

try:
        # Initialize client
        config_manager = EnhancedConfigManager()
        client = UnifiedMaricopaAPIClient(config_manager)

        # Find valid APNs
        print("Step 1: Finding valid APNs...")
        valid_apns = find_valid_apns(client, max_apns=3)

        if not valid_apns:
        print("❌ No valid APNs found. Cannot proceed with detailed testing.")
            return 1
        print(f"✅ Found {len(valid_apns)} valid APNs for testing")

        # Test APN search methods
        print("\nStep 2: Testing APN search methods...")
        apn_results = test_apn_search_detailed(client, valid_apns)

        # Test tax and sales methods
        print("\nStep 3: Testing tax and sales methods...")
        tax_sales_results = test_tax_and_sales_detailed(client, valid_apns)

        # Test endpoint discovery
        print("\nStep 4: Testing endpoint discovery...")
        endpoint_results = test_endpoint_discovery(client)

        # Generate report
        test_duration = time.time() - start_time
        report = generate_detailed_report(
            apn_results, tax_sales_results, endpoint_results, test_duration
        )
        print("\n" + report)

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"detailed_api_test_results_{timestamp}.json"

        detailed_results = {
            "test_metadata": {
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": test_duration,
                "valid_apns": valid_apns,
            },
            "apn_results": apn_results,
            "tax_sales_results": tax_sales_results,
            "endpoint_results": endpoint_results,
        }

        output_dir = Path(__file__).parent
        output_file = output_dir / results_file

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(detailed_results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {output_file}")

except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ TEST EXECUTION ERROR: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
