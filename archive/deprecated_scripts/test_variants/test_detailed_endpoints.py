#!/usr/bin/env python
"""
Test the detailed property API endpoints discovered from network analysis
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import json

import requests


def test_detailed_endpoints():
    """Test detailed property data endpoints"""
    print("Testing Detailed Property Data Endpoints")
    print("=" * 50)
    
    token = "ca1a11a6-adc4-4e0c-a584-36cbb6eb35e5"
    base_url = "https://mcassessor.maricopa.gov"
    apn = "13304014A"
    
    headers = {
        'User-Agent': None,
        'Accept': 'application/json',
        'AUTHORIZATION': token
    }
    
    # Test the detailed endpoints found in network analysis
    endpoints = {
        'valuations': f'/parcel/{apn}/valuations/',
        'residential_details': f'/parcel/{apn}/residential-details/', 
        'improvements': f'/parcel/{apn}/improvements/',
        'sketches': f'/parcel/{apn}/sketches/',
        'mapids': f'/parcel/{apn}/mapids/',
        'rental_details': f'/parcel/{apn}/rental-details/ACCESS%20AL%20LP/'
    }
    
    results = {}
    
    for endpoint_name, endpoint_path in endpoints.items():
        print(f"\nTesting {endpoint_name}: {endpoint_path}")
        print("-" * 30)
        
        try:
            url = base_url + endpoint_path
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    try:
                        data = response.json()
                        results[endpoint_name] = data
                        print(f"SUCCESS - JSON Response!")
                        
                        if isinstance(data, dict):
                            print(f"Keys: {list(data.keys())}")
                            # Show first few fields
                            for key, value in list(data.items())[:3]:
                                print(f"  {key}: {str(value)[:100]}...")
                        elif isinstance(data, list):
                            print(f"Array with {len(data)} items")
                            if data and isinstance(data[0], dict):
                                print(f"First item keys: {list(data[0].keys())}")
                    except json.JSONDecodeError:
                        print(f"Invalid JSON response")
                else:
                    print(f"Non-JSON response: {content_type}")
                    # Check if it's actually JSON without proper content-type
                    try:
                        data = response.json()
                        results[endpoint_name] = data
                        print(f"HIDDEN JSON found!")
                        print(f"Keys: {list(data.keys()) if isinstance(data, dict) else f'Array({len(data)})'}")
                    except:
        print(f"Response text (first 200 chars): {response.text[:200]}")
            else:
                print(f"HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"Request Error: {e}")
    
    print(f"\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if results:
        print(f"Found {len(results)} working detailed endpoints:")
        for endpoint_name, data in results.items():
            if isinstance(data, dict):
                print(f"  {endpoint_name}: {len(data)} fields")
            elif isinstance(data, list):
                print(f"  {endpoint_name}: {len(data)} items")
        
        # Save sample data for analysis
        with open(PROJECT_ROOT / "scripts" / "detailed_api_sample.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nSample data saved to: scripts/detailed_api_sample.json")
    else:
        print("No working detailed endpoints found")
    
    return results

if __name__ == "__main__":
    test_detailed_endpoints()