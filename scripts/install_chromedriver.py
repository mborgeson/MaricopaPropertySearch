#!/usr/bin/env python
"""
ChromeDriver Installation Script for Windows
Automatically downloads and installs the correct ChromeDriver version
"""

import os
import sys
import zipfile
import requests
import subprocess
from pathlib import Path

def get_chrome_version():
    """Get installed Chrome version on Windows"""
    import winreg
    
    try:
        # Try to get Chrome version from registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        return version
    except:
        print("Chrome not found in registry. Trying alternative method...")
        
    # Alternative: Check common installation paths
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, "--version"], 
                    capture_output=True, 
                    text=True
                )
                version = result.stdout.strip().split()[-1]
                return version
            except:
                continue
    
    return None

def download_chromedriver(version):
    """Download appropriate ChromeDriver"""
    project_root = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
    driver_dir = project_root / "drivers"
    driver_dir.mkdir(exist_ok=True)
    
    # Get major version
    major_version = version.split('.')[0]
    
    # Get ChromeDriver version
    version_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
    
    try:
        response = requests.get(version_url)
        driver_version = response.text.strip()
    except:
        print(f"Could not find ChromeDriver for Chrome {major_version}")
        print("Using latest stable version...")
        response = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
        driver_version = response.text.strip()
    
    # Download ChromeDriver
    download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_win32.zip"
    zip_path = driver_dir / "chromedriver.zip"
    
    print(f"Downloading ChromeDriver {driver_version}...")
    response = requests.get(download_url, stream=True)
    
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Extract ChromeDriver
    print("Extracting ChromeDriver...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(driver_dir)
    
    # Clean up
    zip_path.unlink()
    
    # Add to PATH
    driver_path = str(driver_dir)
    if driver_path not in os.environ['PATH']:
        os.environ['PATH'] = f"{driver_path};{os.environ['PATH']}"
    
    print(f"ChromeDriver installed successfully at: {driver_dir}")
    print(f"Version: {driver_version}")
    
    return driver_dir / "chromedriver.exe"

def main():
    print("=" * 50)
    print("ChromeDriver Installation for Windows")
    print("=" * 50)
    print()
    
    # Get Chrome version
    chrome_version = get_chrome_version()
    
    if not chrome_version:
        print("ERROR: Chrome not found!")
        print("Please install Chrome from: https://www.google.com/chrome/")
        sys.exit(1)
    
    print(f"Found Chrome version: {chrome_version}")
    
    # Download and install ChromeDriver
    driver_path = download_chromedriver(chrome_version)
    
    # Test ChromeDriver
    print("\nTesting ChromeDriver...")
    try:
        result = subprocess.run(
            [str(driver_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"ChromeDriver test: {result.stdout.strip()}")
        print("\nChromeDriver is working correctly!")
    except Exception as e:
        print(f"ERROR testing ChromeDriver: {e}")
        sys.exit(1)
    
    print("\nInstallation complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()