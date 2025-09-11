#!/usr/bin/env python
"""
Test the actual API endpoints discovered from browser network analysis
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import requests
import json

def test_real_endpoints():
    """Test the actual endpoints used by the website"""
    
    token = "ca1a11a6-adc4-4e0c-a584-36cbb6eb35e5"
    base_url = "https://mcassessor.maricopa.gov"
    
    # Headers based on API documentation  
    headers = {
        'User-Agent': None,  # API docs specify null
        'Accept': 'application/json',
        'AUTHORIZATION': token
    }
    
    # Also test without token (as website might not require it)
    headers_no_token = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }
    
    # Real endpoints discovered from network analysis
    test_queries = [
        "1811 E Apache Blvd",
        "133-04-014A",
        "ACCESS AL LP"
    ]
    
    endpoints = [
        "/search/rp/",      # Real Property
        "/search/bpp/",     # Business Personal Property  
        "/search/mh/",      # Mobile Home
        "/search/rental/",  # Rental Property
        "/search/sub/"      # Subdivisions
    ]
    
    print("Testing REAL API Endpoints (Discovered from Browser)")
    print("=" * 60)
    print(f"Token: {token[:12]}...")
    print()
    
    working_endpoints = []
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        print("-" * 40)
        
        for endpoint in endpoints:
            for header_name, test_headers in [("WITH TOKEN", headers), ("NO TOKEN", headers_no_token)]:
                try:
                    params = {'q': query}
                    url = base_url + endpoint
                    
                    print(f"  {endpoint} ({header_name})")
                    
                    response = requests.get(url, params=params, headers=test_headers, timeout=10)
                    content_type = response.headers.get('content-type', '')
                    
                    if response.status_code == 200:
                        if 'application/json' in content_type:
                            try:
                                data = response.json()
                                print(f"    SUCCESS - JSON Response!")
                                print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else f'Array({len(data)})'}")
                                
                                if isinstance(data, dict) and data:
                                    # Show first few key-value pairs
                                    for key, value in list(data.items())[:3]:
                                        print(f"      {key}: {str(value)[:60]}...")
                                elif isinstance(data, list) and data:
                                    print(f"    First item: {str(data[0])[:100]}...")
                                
                                working_endpoints.append((endpoint, header_name, query, data))
                                
                            except json.JSONDecodeError:
                                print(f"    FAILED - Claims JSON but invalid")
                        elif 'text/html' in content_type:
                            print(f"    HTML response (not API)")
                        else:
                            print(f"    Status 200, Content: {content_type}")
                            # Check if it might be JSON without proper content-type
                            try:
                                data = response.json()
                                print(f"    HIDDEN JSON - Response is JSON despite content-type!")
                                print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else f'Array({len(data)})'}")
                                working_endpoints.append((endpoint, header_name, query, data))
                            except:
                                pass
                    elif response.status_code == 401:
                        print(f"    UNAUTHORIZED (401)")
                    elif response.status_code == 403:
                        print(f"    FORBIDDEN (403)")
                    elif response.status_code == 404:
                        print(f"    NOT FOUND (404)")
                    else:
                        print(f"    Status: {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    print(f"    TIMEOUT")
                except requests.exceptions.RequestException as e:
                    print(f"    ERROR: {e}")
        
        print()
    
    print("=" * 60)
    print("SUMMARY OF WORKING ENDPOINTS")
    print("=" * 60)
    
    if working_endpoints:
        print("WORKING ENDPOINTS FOUND:")
        for endpoint, auth, query, data in working_endpoints:
            print(f"\n{endpoint} ({auth}) with query '{query}'")
            if isinstance(data, dict):
                for key in list(data.keys())[:5]:
                    value = str(data[key])[:100]
                    print(f"  {key}: {value}...")
            elif isinstance(data, list):
                print(f"  Array with {len(data)} items")
                if data:
                    print(f"  Sample item: {str(data[0])[:100]}...")
            print()
    else:
        print("NO WORKING JSON ENDPOINTS FOUND")
        print("\nThis could mean:")
        print("- Endpoints return HTML for web display, not JSON API")
        print("- API requires different authentication method")
        print("- Need to inspect response content more carefully")
    
    return working_endpoints

if __name__ == "__main__":
    test_real_endpoints()