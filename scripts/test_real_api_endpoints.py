#!/usr/bin/env python
"""
Test real Maricopa County API endpoints to find working data sources
"""

import sys
from pathlib import Path
import requests
import json
import time

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def test_direct_page_access():
    """Test direct access to property search page"""
    print("\n=== Testing Direct Page Access ===")
    
    test_urls = [
        "https://mcassessor.maricopa.gov/parcel/117-01-001A",
        "https://mcassessor.maricopa.gov/search/property/?q=1811+apache+blvd",
        "https://mcassessor.maricopa.gov/property-search",
        "https://mcassessor.maricopa.gov/api/status",
        "https://mcassessor.maricopa.gov/api/search",
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    for url in test_urls:
        try:
            print(f"\nTesting: {url}")
            response = session.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Content Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                # Check if it's JSON
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    try:
                        json_data = response.json()
                        print(f"JSON Response: {json.dumps(json_data, indent=2)[:500]}...")
                    except json.JSONDecodeError:
                        print("Response claims to be JSON but isn't valid JSON")
                else:
                    # Check HTML content for API hints
                    content_preview = response.text[:1000]
                    if 'api' in content_preview.lower():
                        print("Found 'api' mention in HTML content")
                    if 'search' in content_preview.lower():
                        print("Found 'search' functionality in HTML")
                    if 'property' in content_preview.lower():
                        print("Found 'property' references in HTML")
                    
            elif response.status_code == 404:
                print("Endpoint not found")
            elif response.status_code == 403:
                print("Access forbidden - may need authentication")
            else:
                print(f"Unexpected status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        
        time.sleep(1)  # Be respectful
    
    session.close()

def test_network_requests_inspection():
    """Test common API endpoint patterns"""
    print("\n=== Testing Common API Patterns ===")
    
    base_urls = [
        "https://mcassessor.maricopa.gov",
        "https://api.mcassessor.maricopa.gov", 
        "https://mcassessor.maricopa.gov/api",
        "https://services.mcassessor.maricopa.gov"
    ]
    
    endpoints = [
        "/api/search/property",
        "/api/parcel",
        "/api/v1/property",
        "/api/v1/search",
        "/services/property",
        "/rest/property",
        "/webapi/property",
        "/search/api"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'PropertySearchApp/1.0',
        'Accept': 'application/json, */*',
        'Content-Type': 'application/json'
    })
    
    for base_url in base_urls:
        for endpoint in endpoints:
            full_url = base_url + endpoint
            try:
                print(f"Testing: {full_url}")
                response = session.get(full_url, timeout=5)
                
                if response.status_code == 200:
                    print(f"  SUCCESS: {response.status_code}")
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            print(f"  JSON Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                        except:
                            print("  Invalid JSON response")
                    else:
                        print(f"  Content-Type: {content_type}")
                elif response.status_code in [401, 403]:
                    print(f"  AUTH REQUIRED: {response.status_code}")
                elif response.status_code == 404:
                    print(f"  NOT FOUND: {response.status_code}")
                else:
                    print(f"  Status: {response.status_code}")
                    
            except requests.exceptions.RequestException:
                print(f"  FAILED: Connection error")
                
            time.sleep(0.5)  # Rate limiting
    
    session.close()

def test_form_based_search():
    """Test if there's a form-based search we can use"""
    print("\n=== Testing Form-Based Search ===")
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        # First, get the search page
        search_url = "https://mcassessor.maricopa.gov/property-search"
        print(f"Getting search page: {search_url}")
        
        response = session.get(search_url, timeout=10)
        print(f"Search page status: {response.status_code}")
        
        if response.status_code == 200:
            # Look for form elements and CSRF tokens
            content = response.text
            
            # Check for common form patterns
            if '<form' in content:
                print("Found form elements")
            if 'csrf' in content.lower():
                print("Found CSRF token requirements")
            if 'search' in content.lower():
                print("Found search functionality")
            
            # Look for JavaScript API calls
            if 'fetch(' in content or '$.ajax' in content or 'XMLHttpRequest' in content:
                print("Found AJAX/fetch calls - may use JavaScript API")
            
            # Save a snippet for analysis
            with open(PROJECT_ROOT / "scripts" / "search_page_content.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Saved search page content for analysis")
                
        session.close()
        
    except Exception as e:
        print(f"Form test failed: {e}")

def analyze_javascript_network_calls():
    """Look for JavaScript-based API calls"""
    print("\n=== Analyzing JavaScript Network Patterns ===")
    
    # Common patterns to look for in JavaScript
    js_patterns = [
        "fetch('/api/",
        "fetch('/services/",
        "$.ajax({url: '/api/",
        "$.post('/api/",
        "XMLHttpRequest",
        "axios.get('/api/",
        "api.search",
        "property.search"
    ]
    
    try:
        # Get main page JavaScript
        response = requests.get("https://mcassessor.maricopa.gov", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Look for script tags with API references
            import re
            script_urls = re.findall(r'<script[^>]*src=["\']([^"\']*)["\']', content)
            
            print(f"Found {len(script_urls)} script references")
            
            # Check for inline API patterns
            for pattern in js_patterns:
                if pattern in content:
                    print(f"Found pattern: {pattern}")
            
            # Extract any API-like URLs from JavaScript
            api_urls = re.findall(r'["\']([^"\']*api[^"\']*)["\']', content)
            for url in api_urls[:10]:  # Show first 10
                print(f"Potential API URL: {url}")
                
    except Exception as e:
        print(f"JavaScript analysis failed: {e}")

def main():
    """Run all API endpoint tests"""
    print("Maricopa County API Endpoint Discovery")
    print("=" * 50)
    
    print("This script will test various methods to find working API endpoints")
    print("for Maricopa County property data.")
    
    test_direct_page_access()
    test_network_requests_inspection()
    test_form_based_search()
    analyze_javascript_network_calls()
    
    print("\n" + "=" * 50)
    print("API Discovery Complete")
    print("\nNext steps:")
    print("1. Check search_page_content.html for form structures")
    print("2. Use browser developer tools to inspect network calls")
    print("3. Look for working endpoints in the test results above")
    print("4. Update api_client.py with discovered endpoints")

if __name__ == "__main__":
    main()