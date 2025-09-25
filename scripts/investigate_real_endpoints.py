#!/usr/bin/env python
"""
Investigate actual API endpoints used by the Maricopa County website
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
import json

import requests

def investigate_endpoints():
    """Test various potential API endpoint patterns"""

    token = "ca1a11a6-adc4-4e0c-a584-36cbb6eb35e5"
    base_url = "https://mcassessor.maricopa.gov"

    # Headers based on API documentation
    headers = {
        "User-Agent": None,  # API docs specify null
        "Accept": "application/json",
        "AUTHORIZATION": token,
    }

    # Test various endpoint patterns based on common API structures
    test_endpoints = [
        # Documentation-style endpoints
        "/api/v1/properties/search",
        "/api/v1/properties/117-01-001A",
        "/api/v1/status",
        # Website-observed patterns
        "/mcs/api/search",
        "/mcs/api/properties",
        "/mcs/api/property/117-01-001A",
        # Services subdomain (mentioned in contact form)
        "https://services.mcassessor.maricopa.gov/api/properties",
        "https://services.mcassessor.maricopa.gov/api/search",
        # Alternative patterns
        "/services/api/properties",
        "/webapi/properties/search",
        "/rest/v1/properties",
        "/public-api/properties",
    ]
        print("Investigating Real API Endpoints")
        print("=" * 50)
        print(f"Token: {token[:12]}...")
        print()

    working_endpoints = []

    for endpoint in test_endpoints:
try:
            # Handle full URLs vs relative paths
            if endpoint.startswith("https://"):
                url = endpoint
            else:
                url = base_url + endpoint
        print(f"Testing: {endpoint}")

            # Test GET request
            response = requests.get(url, headers=headers, timeout=10)

            content_type = response.headers.get("content-type", "")

            if response.status_code == 200:
                if "application/json" in content_type:
try:
                        data = response.json()
        print(f"  SUCCESS - JSON Response!")
        print(
                            f"  Keys: {list(data.keys()) if isinstance(data, dict) else f'Array({len(data)})'}"
                        )
                        working_endpoints.append((endpoint, "GET", data))
except:
                            print(f"  Invalid JSON but claims application/json")
                elif "text/html" in content_type:
        print(f"  HTML response (likely error page)")
                else:
        print(f"  Status 200, Content-Type: {content_type}")
            elif response.status_code == 401:
        print(f"  UNAUTHORIZED (401) - Token issue")
            elif response.status_code == 403:
        print(f"  FORBIDDEN (403) - Access denied")
            elif response.status_code == 404:
        print(f"  NOT FOUND (404)")
            elif response.status_code == 405:
        print(f"  METHOD NOT ALLOWED (405) - Try POST?")

                # Try POST if GET is not allowed
try:
                    post_response = requests.post(
                        url, headers=headers, json={"q": "117-01-001A"}, timeout=10
                    )
                    if post_response.status_code == 200:
                        if "application/json" in post_response.headers.get(
                            "content-type", ""
                        ):
try:
                                post_data = post_response.json()
        print(f"    POST SUCCESS - JSON Response!")
        print(
                                    f"    Keys: {list(post_data.keys()) if isinstance(post_data, dict) else f'Array({len(post_data)})'}"
                                )
                                working_endpoints.append((endpoint, "POST", post_data))
except:
                                    print(f"    POST returned invalid JSON")
                        else:
        print(
                                f"    POST returned: {post_response.headers.get('content-type')}"
                            )
                    else:
        print(f"    POST Status: {post_response.status_code}")
except Exception as e:
        print(f"    POST failed: {e}")
            else:
        print(f"  Status: {response.status_code}")

except requests.exceptions.Timeout:
        print(f"  TIMEOUT")
except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
        print()
        print("=" * 50)
        print("SUMMARY")
        print("=" * 50)

    if working_endpoints:
        print("WORKING ENDPOINTS FOUND:")
        for endpoint, method, data in working_endpoints:
        print(f"  {method} {endpoint}")
            if isinstance(data, dict):
                for key in list(data.keys())[:3]:
        print(f"    {key}: {str(data[key])[:50]}...")
        print()
    else:
        print("NO WORKING ENDPOINTS FOUND")
        print("\nPossible issues:")
        print("- Token needs activation time")
        print("- Different authentication method required")
        print("- API endpoints are internal/private only")
        print("- Documentation is outdated")

    return working_endpoints


if __name__ == "__main__":
    investigate_endpoints()
