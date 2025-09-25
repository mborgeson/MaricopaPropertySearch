#!/usr/bin/env python
"""
Test Maricopa County API with the configured token
This script tests if our API token works with real Maricopa County endpoints
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import json

import requests
from api_client import MaricopaAPIClient

from config_manager import ConfigManager


def test_api_with_token():
    """Test the API using our configured token"""
    print("Testing Maricopa County API with configured token...")
    print("=" * 60)

    # Load configuration
    config = ConfigManager()
    api_config = config.get_api_config()

    print(f"Base URL: {api_config['base_url']}")
    print(
        f"Token: {api_config['token'][:8]}..."
        if api_config["token"]
        else "No token configured"
    )
    print()

    # Test direct HTTP calls with proper headers
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": None,  # API docs specify null user-agent
            "Accept": "application/json",
            "AUTHORIZATION": api_config["token"],
        }
    )

    # Test endpoints from the API documentation
    test_endpoints = [
        "/api/status",
        "/api/properties/117-01-001A",  # Sample APN from our test data
        "/api/properties/search?q=117-01-001A",
        "/api/properties/search/owner?owner=SMITH",
        "/api/properties/search/address?address=1811+E+APACHE+BLVD",
    ]

    print("Testing endpoints with authentication token:")
    print("-" * 40)

    for endpoint in test_endpoints:
        try:
            url = api_config["base_url"] + endpoint
            print(f"\nTesting: {endpoint}")

            response = session.get(url, timeout=10)

            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        data = response.json()
                        print(f"SUCCESS - JSON Response received")
                        print(
                            f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}"
                        )

                        # Show sample of data
                        if isinstance(data, dict):
                            for key, value in list(data.items())[:3]:
                                print(f"  {key}: {str(value)[:100]}...")
                        elif isinstance(data, list) and data:
                            print(f"  Array with {len(data)} items")
                            if data[0]:
                                print(
                                    f"  First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}"
                                )

                    except json.JSONDecodeError:
                        print("FAILED - Response claims JSON but invalid format")
                        print(
                            f"Response text (first 200 chars): {response.text[:200]}..."
                        )
                else:
                    print(f"FAILED - Not JSON response: {content_type}")
                    if "html" in content_type.lower():
                        print(
                            "Received HTML page - token may be invalid or endpoint incorrect"
                        )
            elif response.status_code == 401:
                print("UNAUTHORIZED - Token is invalid or expired")
            elif response.status_code == 403:
                print("FORBIDDEN - Token doesn't have permission for this endpoint")
            elif response.status_code == 404:
                print("NOT FOUND - Endpoint doesn't exist")
            elif response.status_code == 429:
                print("RATE LIMITED - Too many requests")
            else:
                print(f"ERROR - Status: {response.status_code}")
                print(f"Response: {response.text[:200]}...")

        except requests.exceptions.Timeout:
            print("TIMEOUT - Request took too long")
        except requests.exceptions.RequestException as e:
            print(f"REQUEST ERROR: {e}")

        print("-" * 40)

    session.close()

    # Test using our API client
    print("\n" + "=" * 60)
    print("Testing with MaricopaAPIClient class:")
    print("-" * 40)

    try:
        client = MaricopaAPIClient(config)

        # Test API status
        print("Testing get_api_status()...")
        status = client.get_api_status()
        print(f"API Status: {status}")

        # Test APN search
        print("\nTesting search_by_apn('117-01-001A')...")
        property_data = client.search_by_apn("117-01-001A")

        if property_data:
            print(f"SUCCESS - Found property data:")
            for key, value in list(property_data.items())[:5]:
                print(f"  {key}: {value}")
        else:
            print("No property data returned")

        # Test owner search
        print("\nTesting search_by_owner('SMITH')...")
        owner_results = client.search_by_owner("SMITH", limit=5)

        if owner_results:
            print(f"SUCCESS - Found {len(owner_results)} properties")
            if owner_results[0]:
                print(f"First result keys: {list(owner_results[0].keys())}")
        else:
            print("No owner search results")

        client.close()

    except Exception as e:
        print(f"API CLIENT ERROR: {e}")

    print("\n" + "=" * 60)
    print("API Testing Complete")
    print("\nNext steps:")
    print("1. If successful: Update database with real property data")
    print("2. If unauthorized: Request new API token from Maricopa County")
    print("3. If endpoints not found: Check API documentation for correct URLs")


if __name__ == "__main__":
    test_api_with_token()
