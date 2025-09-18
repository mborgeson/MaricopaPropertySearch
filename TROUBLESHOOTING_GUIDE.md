# MaricopaPropertySearch Troubleshooting Guide

**Comprehensive issue resolution guide for MaricopaPropertySearch application**

Version: Phase 3 Complete (2025-09-18)
Platforms: WSL, Linux, Windows
Architecture: Unified consolidated components

---

## 🚀 Quick Diagnostic Checklist (2-Minute Health Check)

**Run this quick diagnostic to identify common issues immediately:**

```bash
# 1. Check working directory
pwd
# Should be: /path/to/MaricopaPropertySearch

# 2. Check environment variables
echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "DISPLAY: $DISPLAY"
# WSL should show: wayland-0 and :0

# 3. Test platform detection
python src/gui_launcher_unified.py --test-platform
# Should show: Display available: True, Can use GUI: True

# 4. Test core imports
python -c "import PyQt5; import requests; import psycopg2; import beautifulsoup4; print('All core dependencies available')"

# 5. Quick workflow validation
python claudedocs/missouri_ave_test.py
# Should complete in <1 second with successful property data
```

**Expected Performance Benchmarks:**
- Basic property search: < 0.1s
- Comprehensive data collection: < 0.5s
- GUI startup: < 2s
- Platform detection: < 100ms

**If any check fails, jump to the relevant section below.**

---

## 📖 Table of Contents

1. [WSL GUI Issues](#1-wsl-gui-issues)
2. [Import & Module Issues](#2-import--module-issues)
3. [API & Network Issues](#3-api--network-issues)
4. [Database Issues](#4-database-issues)
5. [Performance Issues](#5-performance-issues)
6. [Environment Setup Issues](#6-environment-setup-issues)
7. [Emergency Recovery](#7-emergency-recovery)

---

## 1. WSL GUI Issues

### 1.1 Display Detection Problems

**Symptoms:**
```
[ENV] Display available: False
[ENV] Can use GUI: False
[ERROR] GUI unavailable, falling back to command line
```

**Root Cause:** Application not detecting WSLg/Wayland or X11 display

**Diagnostic Steps:**
```bash
# Check display environment variables
echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"  # Should show: wayland-0
echo "DISPLAY: $DISPLAY"                  # Should show: :0
echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"  # Should show: /run/user/1000

# Test X11 connection
xset q
# Should show: "X.Org version" information

# Test Wayland
ls $XDG_RUNTIME_DIR/wayland-*
# Should show wayland socket files
```

**Resolution:**

**For WSL Users:**
1. **Verify WSLg is installed** (Ubuntu 24.04.3 LTS has this by default):
   ```bash
   wsl --update
   wsl --shutdown
   # Restart WSL
   ```

2. **Check WSL configuration** in Windows:
   ```powershell
   # In PowerShell as Administrator
   wsl --list --verbose
   # Ensure version is 2
   ```

3. **Update display detection** (should be automatic in unified launcher):
   ```bash
   python src/gui_launcher_unified.py --debug-platform
   ```

**For Linux Users:**
1. **Install display server:**
   ```bash
   # For X11
   sudo apt install xorg

   # For Wayland
   sudo apt install wayland-protocols
   ```

2. **Start display server:**
   ```bash
   # Check if display server is running
   ps aux | grep -E "(Xorg|wayland)"
   ```

**Prevention:** Always run from WSL/Linux environment with proper display configuration

**Related Issues:** [1.2 Platform Detection](#12-platform-detection-failures), [6.3 Platform Compatibility](#63-platform-compatibility)

### 1.2 Platform Detection Failures

**Symptoms:**
```
[ENV] Qt platform: offscreen
[ERROR] QApplication: invalid style override passed
[WARNING] Platform detection failed, using fallback
```

**Root Cause:** Qt platform backend not properly detected or configured

**Diagnostic Steps:**
```bash
# Check Qt platform detection
python -c "
import os
print('WAYLAND_DISPLAY:', os.environ.get('WAYLAND_DISPLAY'))
print('DISPLAY:', os.environ.get('DISPLAY'))
print('QT_QPA_PLATFORM:', os.environ.get('QT_QPA_PLATFORM'))
"

# Test Qt5 availability
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 available')"

# Check platform-specific detection
python src/gui_launcher_unified.py --test-gui
```

**Resolution:**

1. **Automatic Detection** (recommended - built into unified launcher):
   ```python
   # This is handled automatically by gui_launcher_unified.py
   # Detection priority: Wayland -> X11 -> Offscreen
   ```

2. **Manual Override** (if automatic detection fails):
   ```bash
   # Force Wayland
   export QT_QPA_PLATFORM=wayland
   python src/gui_launcher_unified.py

   # Force X11
   export QT_QPA_PLATFORM=xcb
   python src/gui_launcher_unified.py

   # Force offscreen (no GUI)
   export QT_QPA_PLATFORM=offscreen
   python src/gui_launcher_unified.py
   ```

3. **Install Qt5 Wayland Support:**
   ```bash
   sudo apt install qt5-wayland qtwayland5
   ```

**Prevention:** Keep Qt5 packages updated and use unified launcher for automatic detection

**Related Issues:** [1.1 Display Detection](#11-display-detection-problems), [1.3 PyQt5 Backend Issues](#13-pyqt5-backend-issues)

### 1.3 PyQt5 Backend Issues

**Symptoms:**
```
ImportError: No module named 'PyQt5'
QApplication: no display found
qt.qpa.plugin: Could not load the Qt platform plugin
```

**Root Cause:** PyQt5 not installed or incompatible with display backend

**Diagnostic Steps:**
```bash
# Check PyQt5 installation
python -c "import PyQt5; print(PyQt5.__file__)"

# Check available Qt plugins
python -c "
from PyQt5.QtWidgets import QApplication
app = QApplication([])
print('Available platforms:', app.platformName())
"

# Check system Qt installation
find /usr -name "*qt5*" -type d 2>/dev/null | head -10
```

**Resolution:**

1. **Install PyQt5:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets

   # Or via pip
   pip install PyQt5
   ```

2. **Install Qt5 platform plugins:**
   ```bash
   sudo apt install qt5-qmake qtbase5-dev qt5-default
   sudo apt install qtwayland5  # For Wayland support
   ```

3. **Fix library dependencies:**
   ```bash
   # Check missing libraries
   ldd $(python -c "import PyQt5.QtWidgets; print(PyQt5.QtWidgets.__file__)")

   # Install missing dependencies
   sudo apt install libxkbcommon-x11-0 libxcb-cursor0
   ```

4. **Test PyQt5 installation:**
   ```bash
   python -c "
   from PyQt5.QtWidgets import QApplication, QLabel
   import sys
   app = QApplication(sys.argv)
   label = QLabel('PyQt5 Test')
   label.show()
   print('PyQt5 working correctly')
   "
   ```

**Prevention:** Install PyQt5 system packages rather than pip packages for better compatibility

**Related Issues:** [6.1 Dependency Installation](#61-dependency-installation), [1.2 Platform Detection](#12-platform-detection-failures)

### 1.4 WSLg Configuration Problems

**Symptoms:**
```
[ENV] WSL detected: True
[ENV] Display available: False
[ERROR] WSLg not properly configured
```

**Root Cause:** WSLg (Windows Subsystem for Linux GUI) configuration issues

**Diagnostic Steps:**
```bash
# Check WSL version
wsl --status
cat /proc/version

# Check WSLg process
ps aux | grep -i wsl

# Check display socket files
ls -la /tmp/.X11-unix/
ls -la $XDG_RUNTIME_DIR/wayland-*

# Test WSLg functionality
glxinfo | grep -i "direct rendering"
```

**Resolution:**

1. **Update WSL to latest version:**
   ```powershell
   # In Windows PowerShell as Administrator
   wsl --update
   wsl --shutdown
   # Restart your WSL distribution
   ```

2. **Verify WSLg installation:**
   ```bash
   # Check if WSLg packages are installed
   dpkg -l | grep -E "(wslu|ubuntu-wsl)"

   # Install if missing
   sudo apt update
   sudo apt install ubuntu-wsl wslu
   ```

3. **Reset WSLg configuration:**
   ```powershell
   # In Windows PowerShell
   wsl --shutdown
   # Wait 10 seconds
   wsl
   ```

4. **Configure WSL for GUI:**
   ```bash
   # Add to ~/.bashrc or ~/.profile
   echo 'export DISPLAY=:0' >> ~/.bashrc
   echo 'export WAYLAND_DISPLAY=wayland-0' >> ~/.bashrc
   source ~/.bashrc
   ```

5. **Test WSLg functionality:**
   ```bash
   # Test with simple GUI app
   sudo apt install x11-apps
   xeyes  # Should display GUI window
   ```

**Prevention:** Keep WSL updated and avoid manual display configuration

**Related Issues:** [1.1 Display Detection](#11-display-detection-problems), [6.3 Platform Compatibility](#63-platform-compatibility)

---

## 2. Import & Module Issues

### 2.1 Relative Import Errors

**Symptoms:**
```
ImportError: attempted relative import with no known parent package
ImportError: attempted relative import beyond top-level package
```

**Root Cause:** Mixed relative and absolute imports, or incorrect working directory

**Diagnostic Steps:**
```bash
# Check current working directory
pwd
# Should be: /path/to/MaricopaPropertySearch (project root)

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check problematic imports
python -c "
import sys
sys.path.insert(0, '.')
from src.gui.enhanced_main_window import EnhancedMainWindow
"
```

**Resolution:**

1. **Ensure correct working directory:**
   ```bash
   cd /path/to/MaricopaPropertySearch
   python src/gui_launcher_unified.py
   ```

2. **Use absolute imports** (already fixed in unified components):
   ```python
   # Correct (absolute imports)
   from src.api_client_unified import UnifiedMaricopaAPIClient
   from src.gui.enhanced_main_window import EnhancedMainWindow
   from src.background_data_collector import BackgroundDataCollectionManager

   # Incorrect (relative imports - avoid these)
   from ..api_client_unified import UnifiedMaricopaAPIClient
   from .enhanced_main_window import EnhancedMainWindow
   from background_data_collector import BackgroundDataCollectionManager
   ```

3. **Fix custom code** (if you've added your own modules):
   ```python
   # In any new files you create, use absolute imports:
   from src.config_manager import ConfigManager
   from src.utils.helpers import utility_function
   ```

4. **Verify import resolution:**
   ```bash
   python -c "
   from src.gui_launcher_unified import UnifiedGUILauncher
   from src.api_client_unified import UnifiedMaricopaAPIClient
   print('All imports successful')
   "
   ```

**Prevention:** Always use absolute imports with `src.` prefix and run from project root

**Related Issues:** [2.2 Module Not Found](#22-module-not-found-errors), [2.4 Working Directory](#24-working-directory-problems)

### 2.2 Module Not Found Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'src'
ModuleNotFoundError: No module named 'PyQt5'
ModuleNotFoundError: No module named 'requests'
```

**Root Cause:** Missing dependencies, incorrect Python path, or wrong working directory

**Diagnostic Steps:**
```bash
# Check if running from correct directory
ls -la src/
# Should show: api_client_unified.py, gui_launcher_unified.py, etc.

# Check Python path includes current directory
python -c "import sys; print('.' in sys.path)"

# Check specific module availability
python -c "import src.gui_launcher_unified"
python -c "import PyQt5"
python -c "import requests"
```

**Resolution:**

1. **Verify working directory:**
   ```bash
   # Navigate to project root
   cd /path/to/MaricopaPropertySearch

   # Verify project structure
   ls -la
   # Should show: src/, claudedocs/, README.md, etc.
   ```

2. **Install missing dependencies:**
   ```bash
   # Install core dependencies
   pip install PyQt5 requests psycopg2-binary beautifulsoup4 lxml

   # Verify installation
   pip list | grep -E "(PyQt5|requests|psycopg2|beautifulsoup4)"
   ```

3. **Fix Python path issues:**
   ```bash
   # Add current directory to Python path (temporary fix)
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"

   # Or run with module flag
   python -m src.gui_launcher_unified
   ```

4. **Use the correct Python interpreter:**
   ```bash
   # Check which Python you're using
   which python
   python --version

   # If using virtual environment
   source venv/bin/activate  # Linux/WSL
   # or
   venv\Scripts\activate     # Windows
   ```

**Prevention:** Always install dependencies and run from project root directory

**Related Issues:** [6.1 Dependency Installation](#61-dependency-installation), [2.1 Relative Import](#21-relative-import-errors)

### 2.3 Python Path Issues

**Symptoms:**
```
ModuleNotFoundError: No module named 'src'
ImportError: cannot import name 'UnifiedMaricopaAPIClient'
sys.path doesn't include current directory
```

**Root Cause:** Python interpreter not finding project modules

**Diagnostic Steps:**
```bash
# Check current Python path
python -c "
import sys
for i, path in enumerate(sys.path):
    print(f'{i}: {path}')
"

# Check if current directory is in path
python -c "
import sys, os
print('Current dir in path:', os.getcwd() in sys.path)
print('Dot in path:', '.' in sys.path)
"

# Test module resolution
python -c "
import sys
sys.path.insert(0, '.')
import src.gui_launcher_unified
print('Module found successfully')
"
```

**Resolution:**

1. **Temporary fix (current session):**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   python src/gui_launcher_unified.py
   ```

2. **Permanent fix for development:**
   ```bash
   # Add to ~/.bashrc or ~/.profile
   echo 'export PYTHONPATH="${PYTHONPATH}:."' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Use proper module execution:**
   ```bash
   # Run as module (recommended)
   python -m src.gui_launcher_unified

   # Or use full path
   PYTHONPATH=. python src/gui_launcher_unified.py
   ```

4. **Create development setup script:**
   ```bash
   # Create setup_env.sh
   cat > setup_env.sh << 'EOF'
   #!/bin/bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   echo "Python path configured for MaricopaPropertySearch"
   EOF

   # Use it
   source setup_env.sh
   python src/gui_launcher_unified.py
   ```

**Prevention:** Use consistent execution method and proper virtual environments

**Related Issues:** [2.2 Module Not Found](#22-module-not-found-errors), [6.4 Development Environment](#64-development-environment-setup)

### 2.4 Working Directory Problems

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'src/config.ini'
ImportError: cannot import name 'UnifiedMaricopaAPIClient'
Application starts but can't find configuration files
```

**Root Cause:** Application not running from correct project root directory

**Diagnostic Steps:**
```bash
# Check current working directory
pwd

# Check if project files exist
ls -la src/
ls -la claudedocs/
ls -la requirements.txt

# Check where application thinks it's running from
python -c "
import os
print('Current working directory:', os.getcwd())
print('Source directory exists:', os.path.exists('src'))
print('GUI launcher exists:', os.path.exists('src/gui_launcher_unified.py'))
"
```

**Resolution:**

1. **Navigate to correct directory:**
   ```bash
   # Find the project directory
   find ~ -name "gui_launcher_unified.py" -type f 2>/dev/null

   # Navigate to project root (parent of src/)
   cd /path/to/MaricopaPropertySearch

   # Verify you're in the right place
   ls -la
   # Should show: src/, claudedocs/, README.md, CLAUDE.md, etc.
   ```

2. **Create directory shortcut:**
   ```bash
   # Add alias to ~/.bashrc
   echo 'alias maricopa="cd /path/to/MaricopaPropertySearch"' >> ~/.bashrc
   source ~/.bashrc

   # Now you can use: maricopa
   ```

3. **Fix application to be directory-agnostic** (advanced):
   ```python
   # In your custom scripts, add:
   import os
   import sys

   # Get the directory of the current script
   script_dir = os.path.dirname(os.path.abspath(__file__))
   project_root = os.path.dirname(script_dir)  # if script is in src/

   # Change to project root
   os.chdir(project_root)

   # Add to Python path
   sys.path.insert(0, project_root)
   ```

4. **Use absolute paths in scripts:**
   ```bash
   # Create run script
   cat > run_maricopa.sh << 'EOF'
   #!/bin/bash
   cd "$(dirname "$0")"  # Change to script directory
   python src/gui_launcher_unified.py "$@"
   EOF

   chmod +x run_maricopa.sh
   ./run_maricopa.sh
   ```

**Prevention:** Always run from project root or use absolute paths

**Related Issues:** [2.1 Relative Import](#21-relative-import-errors), [6.4 Development Environment](#64-development-environment-setup)

---

## 3. API & Network Issues

### 3.1 API Connection Failures

**Symptoms:**
```
ConnectionError: [Errno 111] Connection refused
requests.exceptions.Timeout: Request timed out
API client fallback to web scraping mode
```

**Root Cause:** Network connectivity issues, API server down, or firewall blocking

**Diagnostic Steps:**
```bash
# Test network connectivity
ping google.com

# Test specific API endpoints
curl -I https://mcassessor.maricopa.gov
curl -I https://recorder.maricopa.gov

# Test with application
python -c "
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager
config = EnhancedConfigManager()
client = UnifiedMaricopaAPIClient(config)
result = client.search_by_address('Missouri Ave')
print('API test result:', result)
"

# Check application logs
python claudedocs/missouri_ave_test.py
```

**Resolution:**

1. **Verify network connection:**
   ```bash
   # Check internet connectivity
   wget -q --spider http://google.com && echo "Online" || echo "Offline"

   # Check DNS resolution
   nslookup mcassessor.maricopa.gov
   ```

2. **Test API endpoints manually:**
   ```bash
   # Test Maricopa County endpoints
   curl -v https://mcassessor.maricopa.gov/parcel/10215009
   curl -v https://recorder.maricopa.gov/recdocdata/
   ```

3. **Configure firewall/proxy settings:**
   ```bash
   # Check if behind corporate firewall
   echo $HTTP_PROXY
   echo $HTTPS_PROXY

   # Set proxy if needed
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

4. **Enable fallback mode** (automatic in unified client):
   ```python
   # In enhanced_config_manager.py, enable fallback
   config = EnhancedConfigManager()
   config.set('api', 'enable_fallback', True)
   config.set('web_scraping', 'enabled', True)
   ```

5. **Use mock mode for testing:**
   ```python
   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)
   config.set('api', 'mock_mode', True)
   ```

**Prevention:** Configure fallback systems and test network connectivity regularly

**Related Issues:** [3.3 Timeout Issues](#33-timeout-and-retry-issues), [3.4 Fallback Failures](#34-fallback-system-failures)

### 3.2 Web Scraping Problems

**Symptoms:**
```
ImportError: No module named 'playwright'
requests.exceptions.SSLError: certificate verify failed
BeautifulSoup parsing errors
```

**Root Cause:** Missing dependencies or website changes blocking scraping

**Diagnostic Steps:**
```bash
# Check web scraping dependencies
python -c "import beautifulsoup4; import lxml; print('BeautifulSoup available')"
python -c "import playwright; print('Playwright available')" 2>/dev/null || echo "Playwright not installed"

# Test manual web scraping
python -c "
import requests
from bs4 import BeautifulSoup
url = 'https://mcassessor.maricopa.gov'
response = requests.get(url)
print('Status:', response.status_code)
soup = BeautifulSoup(response.content, 'html.parser')
print('Title:', soup.title.string if soup.title else 'No title')
"

# Check SSL/certificate issues
python -c "
import ssl
import requests
requests.get('https://mcassessor.maricopa.gov', verify=True)
print('SSL verification successful')
"
```

**Resolution:**

1. **Install optional dependencies:**
   ```bash
   # Install Playwright for enhanced web scraping
   pip install playwright
   playwright install chromium

   # Or use basic scraping (already included)
   pip install beautifulsoup4 lxml requests
   ```

2. **Handle SSL certificate issues:**
   ```python
   # Temporary SSL fix (not recommended for production)
   import ssl
   import requests
   from requests.adapters import HTTPAdapter
   from urllib3.util.retry import Retry

   # Configure requests session with SSL handling
   session = requests.Session()
   session.verify = False  # Only for testing
   ```

3. **Configure user agent and headers:**
   ```python
   headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
   }
   response = requests.get(url, headers=headers)
   ```

4. **Use the unified fallback system** (automatic):
   ```python
   # The unified API client automatically handles fallbacks:
   # API -> Web Scraping -> Mock Data
   from src.api_client_unified import UnifiedMaricopaAPIClient
   # Fallback is built-in and automatic
   ```

5. **Enable debug mode for troubleshooting:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   # Run your scraping code to see detailed logs
   ```

**Prevention:** Keep dependencies updated and implement graceful fallbacks

**Related Issues:** [6.1 Dependency Installation](#61-dependency-installation), [3.4 Fallback Failures](#34-fallback-system-failures)

### 3.3 Timeout and Retry Issues

**Symptoms:**
```
requests.exceptions.Timeout: Request timed out after 30 seconds
Connection timeout occurred
Multiple retry attempts failed
```

**Root Cause:** Slow network, overloaded servers, or insufficient timeout values

**Diagnostic Steps:**
```bash
# Test network latency
ping -c 4 mcassessor.maricopa.gov

# Test connection speed
time curl -I https://mcassessor.maricopa.gov

# Check current timeout settings
python -c "
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager
config = EnhancedConfigManager()
client = UnifiedMaricopaAPIClient(config)
print('Timeout settings:', client.timeout)
"
```

**Resolution:**

1. **Increase timeout values:**
   ```python
   # In enhanced_config_manager.py or custom configuration
   config = EnhancedConfigManager()
   config.set('api', 'timeout', 60)  # Increase to 60 seconds
   config.set('api', 'connect_timeout', 10)  # Connection timeout
   config.set('api', 'read_timeout', 50)     # Read timeout
   ```

2. **Configure retry logic** (built into unified client):
   ```python
   # The unified client already includes intelligent retry logic
   # with exponential backoff. To customize:
   config.set('api', 'max_retries', 3)
   config.set('api', 'retry_delay', 1.0)  # Base delay in seconds
   ```

3. **Test with different timeout values:**
   ```bash
   python -c "
   import requests

   # Test different timeout values
   timeouts = [5, 10, 30, 60]
   for timeout in timeouts:
       try:
           response = requests.get('https://mcassessor.maricopa.gov', timeout=timeout)
           print(f'Timeout {timeout}s: Success ({response.status_code})')
           break
       except requests.Timeout:
           print(f'Timeout {timeout}s: Failed')
   "
   ```

4. **Monitor network quality:**
   ```bash
   # Check for packet loss
   ping -c 10 mcassessor.maricopa.gov | grep "packet loss"

   # Check DNS resolution time
   time nslookup mcassessor.maricopa.gov
   ```

5. **Use async operations for better performance:**
   ```python
   # The unified client supports background data collection
   # which doesn't block the main thread
   from src.unified_data_collector import UnifiedDataCollector
   collector = UnifiedDataCollector(config)
   # Background collection handles timeouts gracefully
   ```

**Prevention:** Set appropriate timeouts for your network conditions and use background processing

**Related Issues:** [5.1 Slow Responses](#51-slow-search-responses), [3.1 API Connection](#31-api-connection-failures)

### 3.4 Fallback System Failures

**Symptoms:**
```
All data sources failed
Fallback to mock data unsuccessful
No alternative data source available
```

**Root Cause:** Multiple system failures or configuration issues with fallback chain

**Diagnostic Steps:**
```bash
# Test fallback chain manually
python -c "
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

config = EnhancedConfigManager()
client = UnifiedMaricopaAPIClient(config)

# Test each fallback level
print('Testing API...')
api_result = client._try_api_search('Missouri Ave')
print('API result:', bool(api_result))

print('Testing web scraping...')
web_result = client._try_web_scraping('Missouri Ave')
print('Web result:', bool(web_result))

print('Testing mock...')
mock_result = client._try_mock_data('Missouri Ave')
print('Mock result:', bool(mock_result))
"

# Check configuration
python -c "
from src.enhanced_config_manager import EnhancedConfigManager
config = EnhancedConfigManager()
print('API enabled:', config.get('api', 'enabled', True))
print('Web scraping enabled:', config.get('web_scraping', 'enabled', True))
print('Mock enabled:', config.get('database', 'use_mock', True))
"
```

**Resolution:**

1. **Enable all fallback systems:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Ensure all fallback systems are enabled
   config.set('api', 'enabled', True)
   config.set('web_scraping', 'enabled', True)
   config.set('database', 'use_mock', True)
   config.set('api', 'enable_fallback', True)
   ```

2. **Test each fallback level individually:**
   ```bash
   # Test API only
   python -c "
   from src.api_client_unified import UnifiedMaricopaAPIClient
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()
   config.set('web_scraping', 'enabled', False)
   config.set('database', 'use_mock', False)
   client = UnifiedMaricopaAPIClient(config)
   result = client.search_by_address('Missouri Ave')
   print('API only result:', result)
   "

   # Test web scraping only
   python -c "
   from src.api_client_unified import UnifiedMaricopaAPIClient
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()
   config.set('api', 'enabled', False)
   config.set('database', 'use_mock', False)
   client = UnifiedMaricopaAPIClient(config)
   result = client.search_by_address('Missouri Ave')
   print('Web scraping only result:', result)
   "

   # Test mock only
   python -c "
   from src.api_client_unified import UnifiedMaricopaAPIClient
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()
   config.set('api', 'enabled', False)
   config.set('web_scraping', 'enabled', False)
   config.set('database', 'use_mock', True)
   client = UnifiedMaricopaAPIClient(config)
   result = client.search_by_address('Missouri Ave')
   print('Mock only result:', result)
   "
   ```

3. **Verify mock data is available:**
   ```bash
   python -c "
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)
   db = ThreadSafeDatabaseManager(config)
   properties = db.search_properties_by_address('Missouri')
   print('Mock properties found:', len(properties))
   "
   ```

4. **Reset configuration to defaults:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Reset to safe defaults
   config.set('api', 'enabled', True)
   config.set('api', 'timeout', 30)
   config.set('api', 'max_retries', 3)
   config.set('web_scraping', 'enabled', True)
   config.set('database', 'use_mock', True)
   config.save()  # If save method exists
   ```

**Prevention:** Regularly test all fallback systems and maintain mock data

**Related Issues:** [3.1 API Connection](#31-api-connection-failures), [4.3 Mock Mode Problems](#43-mock-mode-problems)

---

## 4. Database Issues

### 4.1 PostgreSQL Connection Problems

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
FATAL: password authentication failed
Connection to database failed
```

**Root Cause:** PostgreSQL not running, incorrect credentials, or network issues

**Diagnostic Steps:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql
# or
ps aux | grep postgres

# Test connection manually
psql -h localhost -U username -d database_name
# Use the credentials from your config

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Test connection from Python
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='maricopa_properties',
        user='your_username',
        password='your_password'
    )
    print('PostgreSQL connection successful')
    conn.close()
except Exception as e:
    print('PostgreSQL connection failed:', e)
"
```

**Resolution:**

1. **Start PostgreSQL service:**
   ```bash
   # Ubuntu/Debian
   sudo systemctl start postgresql
   sudo systemctl enable postgresql  # Auto-start on boot

   # Check status
   sudo systemctl status postgresql
   ```

2. **Create database and user:**
   ```bash
   # Switch to postgres user
   sudo -u postgres psql

   # In PostgreSQL console:
   CREATE DATABASE maricopa_properties;
   CREATE USER maricopa_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE maricopa_properties TO maricopa_user;
   \q
   ```

3. **Configure database connection:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Set PostgreSQL connection parameters
   config.set('database', 'engine', 'postgresql')
   config.set('database', 'host', 'localhost')
   config.set('database', 'port', 5432)
   config.set('database', 'name', 'maricopa_properties')
   config.set('database', 'user', 'maricopa_user')
   config.set('database', 'password', 'your_password')
   ```

4. **Test database connection:**
   ```bash
   python -c "
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()
   config.set('database', 'engine', 'postgresql')
   db = ThreadSafeDatabaseManager(config)
   print('Database connection test:', db.test_connection())
   "
   ```

5. **Fix authentication issues:**
   ```bash
   # Edit PostgreSQL configuration
   sudo nano /etc/postgresql/*/main/pg_hba.conf

   # Change authentication method (be careful with security)
   # FROM: local   all   all   peer
   # TO:   local   all   all   md5

   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

**Prevention:** Use SQLite for development and PostgreSQL only for production

**Related Issues:** [4.2 SQLite Fallback](#42-sqlite-fallback-issues), [6.4 Development Environment](#64-development-environment-setup)

### 4.2 SQLite Fallback Issues

**Symptoms:**
```
sqlite3.OperationalError: database is locked
sqlite3.OperationalError: no such table
Permission denied when creating SQLite database
```

**Root Cause:** File permissions, database corruption, or concurrent access issues

**Diagnostic Steps:**
```bash
# Check SQLite database file
ls -la *.db *.sqlite*
# or find the database location
find . -name "*.db" -o -name "*.sqlite*"

# Test SQLite manually
sqlite3 database.db ".tables"
sqlite3 database.db ".schema"

# Check file permissions
ls -la database.db

# Test from Python
python -c "
import sqlite3
try:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    print('SQLite connection successful')
    conn.close()
except Exception as e:
    print('SQLite connection failed:', e)
"
```

**Resolution:**

1. **Configure SQLite fallback:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Enable SQLite fallback
   config.set('database', 'engine', 'sqlite')
   config.set('database', 'path', './maricopa_properties.db')
   ```

2. **Fix file permissions:**
   ```bash
   # Ensure write permissions for database directory
   chmod 755 .
   chmod 644 *.db  # If database exists

   # Or create in home directory
   mkdir -p ~/.maricopa_data
   chmod 755 ~/.maricopa_data
   ```

3. **Handle database corruption:**
   ```bash
   # Backup corrupted database
   cp database.db database.db.backup

   # Try to repair
   sqlite3 database.db ".dump" | sqlite3 database_repaired.db

   # Or start fresh
   rm database.db
   # Let application recreate it
   ```

4. **Test SQLite setup:**
   ```bash
   python -c "
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()
   config.set('database', 'engine', 'sqlite')
   config.set('database', 'path', './test.db')
   db = ThreadSafeDatabaseManager(config)
   print('SQLite test:', db.test_connection())
   # Clean up
   import os
   if os.path.exists('./test.db'):
       os.remove('./test.db')
   "
   ```

5. **Handle concurrent access:**
   ```python
   # The ThreadSafeDatabaseManager handles this automatically
   # But if you're using SQLite directly:
   import sqlite3
   conn = sqlite3.connect('database.db', timeout=20.0)
   conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
   ```

**Prevention:** Use proper file permissions and enable WAL mode for SQLite

**Related Issues:** [4.1 PostgreSQL Connection](#41-postgresql-connection-problems), [4.4 Threading Issues](#44-threading-and-connection-pool-issues)

### 4.3 Mock Mode Problems

**Symptoms:**
```
Mock data generation failed
No mock properties found
Mock database not initialized
```

**Root Cause:** Mock data system not properly configured or initialized

**Diagnostic Steps:**
```bash
# Test mock mode configuration
python -c "
from src.enhanced_config_manager import EnhancedConfigManager
config = EnhancedConfigManager()
config.set('database', 'use_mock', True)
print('Mock mode enabled:', config.get('database', 'use_mock'))
"

# Test mock data generation
python -c "
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager
config = EnhancedConfigManager()
config.set('database', 'use_mock', True)
db = ThreadSafeDatabaseManager(config)
properties = db.search_properties_by_address('Missouri')
print('Mock properties found:', len(properties))
"

# Test full mock workflow
python claudedocs/missouri_ave_test.py
```

**Resolution:**

1. **Enable mock mode:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Enable mock mode
   config.set('database', 'use_mock', True)
   config.set('api', 'mock_mode', True)  # If available
   ```

2. **Initialize mock data:**
   ```python
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)
   db = ThreadSafeDatabaseManager(config)

   # Initialize mock data (if method exists)
   if hasattr(db, 'initialize_mock_data'):
       db.initialize_mock_data()
   ```

3. **Test mock data availability:**
   ```bash
   python -c "
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)
   db = ThreadSafeDatabaseManager(config)

   # Test various mock queries
   test_queries = ['Missouri', '10000', 'Ave', 'Property']
   for query in test_queries:
       results = db.search_properties_by_address(query)
       print(f'Query {query}: {len(results)} results')
   "
   ```

4. **Verify mock mode in API client:**
   ```bash
   python -c "
   from src.api_client_unified import UnifiedMaricopaAPIClient
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)
   client = UnifiedMaricopaAPIClient(config)

   result = client.search_by_address('10000 W Missouri Ave')
   print('Mock API result:', result is not None)
   if result:
       print('Property data:', result.get('address', 'No address'))
   "
   ```

5. **Reset mock system:**
   ```python
   # If mock system gets corrupted, reset it
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Disable and re-enable mock mode
   config.set('database', 'use_mock', False)
   config.set('database', 'use_mock', True)

   # Reinitialize database manager
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   db = ThreadSafeDatabaseManager(config)
   ```

**Prevention:** Always test mock mode as part of development workflow

**Related Issues:** [3.4 Fallback Failures](#34-fallback-system-failures), [5.4 Background Collection](#54-background-collection-problems)

### 4.4 Threading and Connection Pool Issues

**Symptoms:**
```
database connection pool exhausted
Threading deadlock detected
Connection leak in database pool
SQLite database is locked
```

**Root Cause:** Concurrent database access issues or connection pool configuration

**Diagnostic Steps:**
```bash
# Check for database locks
sudo lsof | grep database.db  # For SQLite
ps aux | grep postgres       # For PostgreSQL

# Test threading behavior
python -c "
import threading
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager

config = EnhancedConfigManager()
config.set('database', 'use_mock', True)

def test_thread():
    db = ThreadSafeDatabaseManager(config)
    results = db.search_properties_by_address('Missouri')
    print(f'Thread {threading.current_thread().name}: {len(results)} results')

# Run multiple threads
threads = []
for i in range(5):
    t = threading.Thread(target=test_thread, name=f'Thread-{i}')
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print('Threading test completed')
"

# Monitor connection pool
python -c "
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager
config = EnhancedConfigManager()
db = ThreadSafeDatabaseManager(config)
if hasattr(db, 'get_pool_status'):
    print('Pool status:', db.get_pool_status())
"
```

**Resolution:**

1. **Configure connection pool settings:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Adjust pool settings
   config.set('database', 'pool_size', 10)
   config.set('database', 'max_overflow', 20)
   config.set('database', 'pool_timeout', 30)
   config.set('database', 'pool_recycle', 3600)  # 1 hour
   ```

2. **Enable WAL mode for SQLite:**
   ```python
   # For SQLite, enable Write-Ahead Logging
   config.set('database', 'sqlite_wal_mode', True)
   ```

3. **Use proper connection management:**
   ```python
   # The ThreadSafeDatabaseManager handles this automatically
   # But for custom code, ensure proper connection cleanup:

   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   config = EnhancedConfigManager()

   db = ThreadSafeDatabaseManager(config)
   try:
       results = db.search_properties_by_address('Missouri')
       # Process results
   finally:
       # Connections are automatically returned to pool
       pass
   ```

4. **Debug connection leaks:**
   ```bash
   python -c "
   import gc
   import threading
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)

   # Check for memory leaks
   before = len(gc.get_objects())

   db = ThreadSafeDatabaseManager(config)
   for i in range(100):
       results = db.search_properties_by_address('Missouri')

   after = len(gc.get_objects())
   print(f'Objects before: {before}, after: {after}, diff: {after - before}')
   "
   ```

5. **Handle deadlocks:**
   ```python
   # Use timeout and retry logic (built into ThreadSafeDatabaseManager)
   config.set('database', 'lock_timeout', 30)
   config.set('database', 'retry_on_deadlock', True)
   config.set('database', 'max_deadlock_retries', 3)
   ```

**Prevention:** Use the ThreadSafeDatabaseManager and configure appropriate pool settings

**Related Issues:** [5.3 Threading Issues](#53-threading-issues), [4.2 SQLite Fallback](#42-sqlite-fallback-issues)

---

## 5. Performance Issues

### 5.1 Slow Search Responses

**Symptoms:**
```
Property search taking >5 seconds
API responses timing out
GUI freezing during searches
```

**Root Cause:** Network latency, inefficient queries, or blocking operations

**Diagnostic Steps:**
```bash
# Benchmark current performance
time python claudedocs/missouri_ave_test.py

# Test individual components
python -c "
import time
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

config = EnhancedConfigManager()
client = UnifiedMaricopaAPIClient(config)

start = time.time()
result = client.search_by_address('10000 W Missouri Ave')
elapsed = time.time() - start

print(f'Search completed in {elapsed:.3f} seconds')
print(f'Result found: {result is not None}')
"

# Check network latency
ping -c 5 mcassessor.maricopa.gov
```

**Expected Performance Benchmarks:**
- Basic property search: < 0.1s
- Comprehensive data collection: < 0.5s
- API response time: < 2s
- GUI responsiveness: < 100ms

**Resolution:**

1. **Enable background data collection:**
   ```python
   from src.unified_data_collector import UnifiedDataCollector
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   collector = UnifiedDataCollector(config)

   # Use background collection for non-blocking operations
   collector.start_background_collection()
   ```

2. **Configure performance optimizations:**
   ```python
   config = EnhancedConfigManager()

   # Optimize API settings
   config.set('api', 'timeout', 10)  # Reduce timeout
   config.set('api', 'concurrent_requests', 3)  # Parallel requests
   config.set('api', 'cache_enabled', True)  # Enable caching

   # Optimize database settings
   config.set('database', 'pool_size', 5)
   config.set('database', 'connection_timeout', 5)
   ```

3. **Use progressive data loading:**
   ```python
   # The unified API client supports progressive loading:
   # 1. Fast basic search (0.04s)
   # 2. Detailed information (0.33s)
   # 3. Background comprehensive data

   client = UnifiedMaricopaAPIClient(config)

   # Quick basic search first
   basic_result = client.search_by_address('Missouri Ave', mode='basic')

   # Then detailed information
   if basic_result:
       detailed_result = client.get_comprehensive_property_info(
           basic_result['apn'], background=True
       )
   ```

4. **Enable mock mode for testing:**
   ```python
   # For development/testing, use mock mode for instant responses
   config.set('database', 'use_mock', True)
   config.set('api', 'mock_mode', True)
   ```

5. **Monitor performance:**
   ```bash
   # Regular performance validation
   python -c "
   import time
   from src.api_client_unified import UnifiedMaricopaAPIClient
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   client = UnifiedMaricopaAPIClient(config)

   test_addresses = [
       '10000 W Missouri Ave',
       '12345 N Main St',
       '67890 E Central Ave'
   ]

   for address in test_addresses:
       start = time.time()
       result = client.search_by_address(address)
       elapsed = time.time() - start
       status = 'PASS' if elapsed < 1.0 else 'FAIL'
       print(f'{address}: {elapsed:.3f}s [{status}]')
   "
   ```

**Prevention:** Use background processing and monitor performance regularly

**Related Issues:** [3.3 Timeout Issues](#33-timeout-and-retry-issues), [5.3 Threading Issues](#53-threading-issues)

### 5.2 Memory Usage Problems

**Symptoms:**
```
Application consuming excessive memory
Out of memory errors
Memory leaks in long-running processes
```

**Root Cause:** Memory leaks, large data caching, or inefficient data structures

**Diagnostic Steps:**
```bash
# Monitor memory usage
top -p $(pgrep -f "python.*maricopa")
# or
ps aux | grep python | grep maricopa

# Monitor Python memory usage
python -c "
import psutil
import os

process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f'Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB')

# Test for memory leaks
import gc
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

config = EnhancedConfigManager()
client = UnifiedMaricopaAPIClient(config)

for i in range(100):
    result = client.search_by_address('Missouri Ave')
    if i % 10 == 0:
        gc.collect()
        memory_info = process.memory_info()
        print(f'Iteration {i}: {memory_info.rss / 1024 / 1024:.2f} MB')
"
```

**Resolution:**

1. **Configure memory limits:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()

   # Limit cache sizes
   config.set('api', 'cache_max_size', 100)  # Max cached responses
   config.set('database', 'pool_size', 5)    # Limit connections
   config.set('data_collector', 'max_concurrent', 3)  # Limit threads
   ```

2. **Enable garbage collection:**
   ```python
   import gc

   # Force garbage collection periodically
   gc.collect()

   # Enable automatic garbage collection
   gc.set_threshold(700, 10, 10)  # Adjust thresholds
   ```

3. **Use memory-efficient data structures:**
   ```python
   # In custom code, prefer generators over lists for large datasets
   def process_properties():
       # Instead of loading all data at once:
       # properties = db.get_all_properties()  # Memory intensive

       # Use generator:
       for property_batch in db.get_properties_batch(batch_size=100):
           yield property_batch
   ```

4. **Monitor memory usage:**
   ```bash
   # Create memory monitoring script
   cat > monitor_memory.py << 'EOF'
   import psutil
   import time
   import subprocess

   def monitor_maricopa_memory():
       while True:
           try:
               # Find Maricopa processes
               processes = []
               for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                   if 'python' in proc.info['name']:
                       cmdline = proc.cmdline()
                       if any('maricopa' in arg.lower() for arg in cmdline):
                           processes.append(proc)

               total_memory = sum(p.memory_info().rss for p in processes)
               print(f'{time.strftime("%H:%M:%S")} - Memory: {total_memory / 1024 / 1024:.2f} MB')

               time.sleep(5)
           except KeyboardInterrupt:
               break

   if __name__ == '__main__':
       monitor_maricopa_memory()
   EOF

   python monitor_memory.py
   ```

5. **Clear caches periodically:**
   ```python
   # Add cache clearing to long-running processes
   from src.api_client_unified import UnifiedMaricopaAPIClient
   config = EnhancedConfigManager()
   client = UnifiedMaricopaAPIClient(config)

   # Clear cache periodically
   if hasattr(client, 'clear_cache'):
       client.clear_cache()
   ```

**Prevention:** Monitor memory usage and implement cache limits

**Related Issues:** [5.3 Threading Issues](#53-threading-issues), [4.4 Connection Pool](#44-threading-and-connection-pool-issues)

### 5.3 Threading Issues

**Symptoms:**
```
Thread deadlocks
Race conditions in data access
Threading synchronization errors
GUI freezing during background operations
```

**Root Cause:** Improper thread synchronization or blocking operations in GUI thread

**Diagnostic Steps:**
```bash
# Monitor thread count
python -c "
import threading
import time
from src.unified_data_collector import UnifiedDataCollector
from src.enhanced_config_manager import EnhancedConfigManager

config = EnhancedConfigManager()
collector = UnifiedDataCollector(config)

print('Initial threads:', threading.active_count())
collector.start_background_collection()
time.sleep(2)
print('After background start:', threading.active_count())

# List active threads
for thread in threading.enumerate():
    print(f'Thread: {thread.name}, alive: {thread.is_alive()}')
"

# Check for deadlocks
python -c "
import signal
import threading
import traceback

def dump_threads(signum, frame):
    for thread_id, frame in sys._current_frames().items():
        print(f'Thread {thread_id}:')
        traceback.print_stack(frame)
        print()

signal.signal(signal.SIGUSR1, dump_threads)
print('Send SIGUSR1 to dump thread stacks')
# kill -USR1 <python_pid>
"
```

**Resolution:**

1. **Use the unified data collector** (thread-safe by design):
   ```python
   from src.unified_data_collector import UnifiedDataCollector
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   collector = UnifiedDataCollector(config)

   # Built-in thread safety and management
   collector.start_background_collection()
   ```

2. **Configure threading limits:**
   ```python
   config = EnhancedConfigManager()

   # Limit concurrent operations
   config.set('data_collector', 'max_threads', 3)
   config.set('api', 'max_concurrent_requests', 2)
   config.set('database', 'pool_size', 5)
   ```

3. **Use proper synchronization:**
   ```python
   import threading
   from queue import Queue

   # Use thread-safe data structures
   result_queue = Queue()

   # Use locks for shared resources
   resource_lock = threading.Lock()

   def thread_safe_operation():
       with resource_lock:
           # Critical section
           pass
   ```

4. **Implement timeout and cancellation:**
   ```python
   import threading
   import time

   def background_task(stop_event):
       while not stop_event.is_set():
           # Do work
           time.sleep(0.1)

           # Check for cancellation
           if stop_event.wait(timeout=0):
               break

   # Usage
   stop_event = threading.Event()
   thread = threading.Thread(target=background_task, args=(stop_event,))
   thread.start()

   # Later, to stop:
   stop_event.set()
   thread.join(timeout=5)
   ```

5. **Debug threading issues:**
   ```bash
   python -c "
   import threading
   import time
   import logging

   # Enable thread debug logging
   logging.basicConfig(level=logging.DEBUG)

   # Set thread name for debugging
   threading.current_thread().name = 'MainThread'

   from src.unified_data_collector import UnifiedDataCollector
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()
   collector = UnifiedDataCollector(config)

   print('Starting background collection...')
   collector.start_background_collection()

   time.sleep(5)

   print('Active threads:')
   for thread in threading.enumerate():
       print(f'  {thread.name}: {thread.is_alive()}')

   print('Stopping background collection...')
   collector.stop_background_collection()
   "
   ```

**Prevention:** Use the unified components which include proper thread management

**Related Issues:** [5.2 Memory Usage](#52-memory-usage-problems), [4.4 Connection Pool](#44-threading-and-connection-pool-issues)

### 5.4 Background Collection Problems

**Symptoms:**
```
Background data collection not starting
Progress tracking not updating
Background threads hanging or crashing
```

**Root Cause:** Threading issues, resource conflicts, or configuration problems

**Diagnostic Steps:**
```bash
# Test background collection
python -c "
from src.unified_data_collector import UnifiedDataCollector
from src.enhanced_config_manager import EnhancedConfigManager
import time

config = EnhancedConfigManager()
collector = UnifiedDataCollector(config)

print('Starting background collection test...')
collector.start_background_collection()

# Wait and check status
time.sleep(3)
if hasattr(collector, 'is_running'):
    print('Collection running:', collector.is_running())

if hasattr(collector, 'get_progress'):
    progress = collector.get_progress()
    print('Progress:', progress)

collector.stop_background_collection()
print('Background collection test completed')
"

# Check for resource conflicts
lsof -p $(pgrep -f "python.*maricopa") | grep -E "(database|socket)"
```

**Resolution:**

1. **Enable background collection properly:**
   ```python
   from src.unified_data_collector import UnifiedDataCollector
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()

   # Configure background collection
   config.set('data_collector', 'background_enabled', True)
   config.set('data_collector', 'progress_tracking', True)
   config.set('data_collector', 'max_background_threads', 2)

   collector = UnifiedDataCollector(config)
   ```

2. **Handle collection errors:**
   ```python
   import logging

   # Enable logging to see background collection issues
   logging.basicConfig(level=logging.INFO)

   try:
       collector.start_background_collection()
   except Exception as e:
       print(f'Background collection failed to start: {e}')
       # Fall back to synchronous collection
       collector.collect_synchronously()
   ```

3. **Monitor collection progress:**
   ```python
   import time
   import threading

   def monitor_progress(collector):
       while collector.is_running():
           if hasattr(collector, 'get_progress'):
               progress = collector.get_progress()
               print(f'Progress: {progress}%')
           time.sleep(1)

   # Start monitoring in separate thread
   monitor_thread = threading.Thread(target=monitor_progress, args=(collector,))
   monitor_thread.daemon = True
   monitor_thread.start()
   ```

4. **Implement proper cleanup:**
   ```python
   import atexit

   def cleanup_background_collection():
       if collector.is_running():
           collector.stop_background_collection()

   # Register cleanup function
   atexit.register(cleanup_background_collection)
   ```

5. **Test collection robustness:**
   ```bash
   python -c "
   from src.unified_data_collector import UnifiedDataCollector
   from src.enhanced_config_manager import EnhancedConfigManager
   import time
   import signal
   import sys

   config = EnhancedConfigManager()
   collector = UnifiedDataCollector(config)

   def signal_handler(sig, frame):
       print('Stopping background collection...')
       collector.stop_background_collection()
       sys.exit(0)

   signal.signal(signal.SIGINT, signal_handler)

   print('Starting robust collection test...')
   collector.start_background_collection()

   # Run for 30 seconds or until interrupted
   try:
       time.sleep(30)
   except KeyboardInterrupt:
       pass

   collector.stop_background_collection()
   print('Collection test completed')
   "
   ```

**Prevention:** Use the unified data collector and implement proper error handling

**Related Issues:** [5.3 Threading Issues](#53-threading-issues), [3.3 Timeout Issues](#33-timeout-and-retry-issues)

---

## 6. Environment Setup Issues

### 6.1 Dependency Installation

**Symptoms:**
```
ImportError: No module named 'PyQt5'
pip install failed with compilation errors
Package conflicts between system and pip packages
```

**Root Cause:** Missing system packages, conflicting installations, or outdated pip

**Diagnostic Steps:**
```bash
# Check Python and pip versions
python --version
pip --version

# Check installed packages
pip list | grep -E "(PyQt5|requests|psycopg2|beautifulsoup4)"

# Check for conflicting installations
python -c "
import sys
print('Python path:')
for path in sys.path:
    print(f'  {path}')

try:
    import PyQt5
    print(f'PyQt5 location: {PyQt5.__file__}')
except ImportError as e:
    print(f'PyQt5 import error: {e}')
"

# Check system packages
dpkg -l | grep -E "(python3-pyqt5|python3-requests)"
```

**Resolution:**

1. **Install system packages first** (recommended):
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets
   sudo apt install python3-requests python3-psycopg2
   sudo apt install python3-bs4 python3-lxml

   # Verify system installation
   python3 -c "import PyQt5; import requests; import psycopg2; import bs4; print('System packages OK')"
   ```

2. **Alternative: pip installation** (if system packages unavailable):
   ```bash
   # Update pip first
   pip install --upgrade pip

   # Install core dependencies
   pip install PyQt5==5.15.7
   pip install requests==2.28.2
   pip install psycopg2-binary==2.9.5
   pip install beautifulsoup4==4.11.1
   pip install lxml==4.9.2

   # Verify pip installation
   python -c "import PyQt5; import requests; import psycopg2; import bs4; print('Pip packages OK')"
   ```

3. **Handle compilation errors:**
   ```bash
   # Install build dependencies
   sudo apt install build-essential python3-dev
   sudo apt install libpq-dev  # For psycopg2
   sudo apt install qt5-qmake qtbase5-dev  # For PyQt5

   # For ARM64/Apple Silicon
   export ARCHFLAGS="-arch arm64"
   pip install psycopg2-binary
   ```

4. **Use virtual environment** (recommended for development):
   ```bash
   # Create virtual environment
   python3 -m venv maricopa_env
   source maricopa_env/bin/activate

   # Install requirements
   pip install --upgrade pip
   pip install -r requirements.txt

   # Verify installation
   python -c "
   import PyQt5
   import requests
   import psycopg2
   import bs4
   print('Virtual environment setup complete')
   "
   ```

5. **Fix package conflicts:**
   ```bash
   # Remove conflicting packages
   pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
   sudo apt remove python3-pyqt5

   # Clean reinstall
   sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets

   # Or use pip if system packages don't work
   pip install PyQt5
   ```

**Prevention:** Use system packages when available, virtual environments for development

**Related Issues:** [1.3 PyQt5 Backend Issues](#13-pyqt5-backend-issues), [6.4 Development Environment](#64-development-environment-setup)

### 6.2 Configuration Problems

**Symptoms:**
```
Configuration file not found
Invalid configuration values
Configuration conflicts between environment and files
```

**Root Cause:** Missing configuration files, incorrect paths, or environment variable conflicts

**Diagnostic Steps:**
```bash
# Check for configuration files
find . -name "*.ini" -o -name "*.conf" -o -name "config.*"

# Check environment variables
env | grep -i maricopa
env | grep -E "(DATABASE|API|GUI)"

# Test configuration loading
python -c "
from src.enhanced_config_manager import EnhancedConfigManager
try:
    config = EnhancedConfigManager()
    print('Configuration loaded successfully')
    print('Available sections:', config.sections() if hasattr(config, 'sections') else 'N/A')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

**Resolution:**

1. **Create default configuration:**
   ```bash
   # Create config directory if it doesn't exist
   mkdir -p config/

   # Create default configuration file
   cat > config/default.ini << 'EOF'
   [database]
   engine = sqlite
   path = ./maricopa_properties.db
   use_mock = true

   [api]
   enabled = true
   timeout = 30
   max_retries = 3

   [gui]
   platform = auto
   theme = default

   [logging]
   level = INFO
   file = maricopa.log
   EOF
   ```

2. **Use enhanced configuration manager:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager

   # Load configuration with defaults
   config = EnhancedConfigManager()

   # Set safe defaults
   config.set('database', 'use_mock', True)
   config.set('api', 'timeout', 30)
   config.set('gui', 'platform', 'auto')
   ```

3. **Handle environment variable overrides:**
   ```python
   import os
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()

   # Allow environment variables to override config
   if os.environ.get('MARICOPA_DATABASE_URL'):
       config.set('database', 'url', os.environ['MARICOPA_DATABASE_URL'])

   if os.environ.get('MARICOPA_API_TIMEOUT'):
       config.set('api', 'timeout', int(os.environ['MARICOPA_API_TIMEOUT']))
   ```

4. **Validate configuration:**
   ```bash
   python -c "
   from src.enhanced_config_manager import EnhancedConfigManager

   config = EnhancedConfigManager()

   # Validate critical settings
   required_settings = {
       'database': ['engine'],
       'api': ['timeout'],
   }

   for section, keys in required_settings.items():
       for key in keys:
           try:
               value = config.get(section, key)
               print(f'{section}.{key}: {value}')
           except Exception as e:
               print(f'Missing {section}.{key}: {e}')
   "
   ```

5. **Reset configuration to defaults:**
   ```python
   from src.enhanced_config_manager import EnhancedConfigManager

   # Reset to safe defaults
   config = EnhancedConfigManager()

   # Database settings
   config.set('database', 'engine', 'sqlite')
   config.set('database', 'use_mock', True)

   # API settings
   config.set('api', 'enabled', True)
   config.set('api', 'timeout', 30)
   config.set('api', 'max_retries', 3)

   # GUI settings
   config.set('gui', 'platform', 'auto')

   # Save configuration if method exists
   if hasattr(config, 'save'):
       config.save()
   ```

**Prevention:** Use the enhanced configuration manager with sensible defaults

**Related Issues:** [4.1 PostgreSQL Connection](#41-postgresql-connection-problems), [1.2 Platform Detection](#12-platform-detection-failures)

### 6.3 Platform Compatibility

**Symptoms:**
```
Platform detection failed
Qt platform not supported
WSL-specific features not working
Windows path issues in WSL
```

**Root Cause:** Platform-specific incompatibilities or missing platform support

**Diagnostic Steps:**
```bash
# Check platform information
python -c "
import platform
import os
print(f'Platform: {platform.system()}')
print(f'Machine: {platform.machine()}')
print(f'Platform: {platform.platform()}')
print(f'WSL: {\"Microsoft\" in platform.release()}')
print(f'Is WSL: {os.path.exists(\"/proc/version\") and \"microsoft\" in open(\"/proc/version\").read().lower()}')
"

# Check display environment
echo "Platform: $(uname -s)"
echo "WSL version: $(cat /proc/version | grep -o 'Microsoft.*')"
echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "DISPLAY: $DISPLAY"

# Test GUI launcher platform detection
python src/gui_launcher_unified.py --test-platform
```

**Resolution:**

1. **Use unified platform detection** (automatic in gui_launcher_unified.py):
   ```python
   from src.gui_launcher_unified import UnifiedGUILauncher

   launcher = UnifiedGUILauncher()

   # Automatic platform detection:
   # - WSL with WSLg (Wayland preferred)
   # - Linux with X11 or Wayland
   # - Windows native
   # - Headless/server environments
   ```

2. **Handle WSL-specific issues:**
   ```bash
   # Ensure WSLg is properly configured
   echo $WAYLAND_DISPLAY  # Should show: wayland-0
   echo $DISPLAY          # Should show: :0

   # Fix WSL display if needed
   export WAYLAND_DISPLAY=wayland-0
   export DISPLAY=:0

   # Add to ~/.bashrc for persistence
   echo 'export WAYLAND_DISPLAY=wayland-0' >> ~/.bashrc
   echo 'export DISPLAY=:0' >> ~/.bashrc
   ```

3. **Handle Linux distribution differences:**
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-pyqt5 qtwayland5

   # CentOS/RHEL/Fedora
   sudo dnf install python3-qt5 qt5-qtwayland

   # Arch Linux
   sudo pacman -S python-pyqt5 qt5-wayland
   ```

4. **Handle Windows-specific issues:**
   ```powershell
   # In Windows PowerShell
   # Update WSL if running in WSL
   wsl --update

   # For native Windows (if needed)
   # Install Qt5 for Windows
   pip install PyQt5
   ```

5. **Implement platform-specific workarounds:**
   ```python
   import platform
   import os

   def get_platform_config():
       system = platform.system()
       is_wsl = "microsoft" in platform.release().lower()

       if system == "Linux" and is_wsl:
           # WSL configuration
           return {
               'qt_platform': 'wayland' if os.environ.get('WAYLAND_DISPLAY') else 'xcb',
               'display_scaling': 1.0,
               'font_family': 'Ubuntu'
           }
       elif system == "Linux":
           # Native Linux
           return {
               'qt_platform': 'xcb',
               'display_scaling': 1.0,
               'font_family': 'Sans'
           }
       elif system == "Windows":
           # Native Windows
           return {
               'qt_platform': 'windows',
               'display_scaling': 1.25,
               'font_family': 'Segoe UI'
           }
       else:
           # Fallback
           return {
               'qt_platform': 'offscreen',
               'display_scaling': 1.0,
               'font_family': 'monospace'
           }
   ```

**Prevention:** Use the unified launcher and test on target platforms

**Related Issues:** [1.1 Display Detection](#11-display-detection-problems), [1.4 WSLg Configuration](#14-wslg-configuration-problems)

### 6.4 Development Environment Setup

**Symptoms:**
```
Inconsistent behavior between environments
IDE not recognizing project structure
Debugging tools not working
```

**Root Cause:** Inconsistent development environment setup or missing development tools

**Diagnostic Steps:**
```bash
# Check development environment
which python
python --version
which pip
pip --version

# Check project structure recognition
python -c "
import sys
import os
print('Current directory:', os.getcwd())
print('Python path:')
for path in sys.path:
    print(f'  {path}')
print('Can import project:', 'src' in os.listdir('.'))
"

# Check development tools
which git
git --version
python -c "import pdb; print('pdb available')"
```

**Resolution:**

1. **Set up proper development environment:**
   ```bash
   # Navigate to project root
   cd /path/to/MaricopaPropertySearch

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # Linux/WSL
   # or
   venv\Scripts\activate     # Windows

   # Install development dependencies
   pip install --upgrade pip
   pip install -r requirements.txt

   # Install development tools
   pip install pytest pylint black isort
   ```

2. **Configure IDE (VS Code example):**
   ```json
   # .vscode/settings.json
   {
       "python.defaultInterpreterPath": "./venv/bin/python",
       "python.linting.enabled": true,
       "python.linting.pylintEnabled": true,
       "python.formatting.provider": "black",
       "python.sortImports.args": ["--profile", "black"],
       "files.exclude": {
           "**/__pycache__": true,
           "**/*.pyc": true
       }
   }
   ```

3. **Set up debugging:**
   ```json
   # .vscode/launch.json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Python: Current File",
               "type": "python",
               "request": "launch",
               "program": "${file}",
               "console": "integratedTerminal",
               "cwd": "${workspaceFolder}",
               "env": {
                   "PYTHONPATH": "${workspaceFolder}"
               }
           },
           {
               "name": "Launch GUI",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/src/gui_launcher_unified.py",
               "console": "integratedTerminal",
               "cwd": "${workspaceFolder}"
           }
       ]
   }
   ```

4. **Create development scripts:**
   ```bash
   # Create dev_setup.sh
   cat > dev_setup.sh << 'EOF'
   #!/bin/bash
   set -e

   echo "Setting up MaricopaPropertySearch development environment..."

   # Activate virtual environment
   if [ ! -d "venv" ]; then
       python3 -m venv venv
   fi
   source venv/bin/activate

   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt

   # Install development tools
   pip install pytest pylint black isort mypy

   # Set environment variables
   export PYTHONPATH="$(pwd):$PYTHONPATH"

   echo "Development environment ready!"
   echo "Run: source venv/bin/activate"
   EOF

   chmod +x dev_setup.sh
   ./dev_setup.sh
   ```

5. **Set up testing environment:**
   ```bash
   # Create test runner script
   cat > run_tests.sh << 'EOF'
   #!/bin/bash
   source venv/bin/activate

   echo "Running Missouri Avenue test..."
   python claudedocs/missouri_ave_test.py

   echo "Running platform tests..."
   python src/gui_launcher_unified.py --test-platform

   echo "Running import tests..."
   python -c "
   from src.api_client_unified import UnifiedMaricopaAPIClient
   from src.unified_data_collector import UnifiedDataCollector
   from src.threadsafe_database_manager import ThreadSafeDatabaseManager
   from src.gui_launcher_unified import UnifiedGUILauncher
   print('All imports successful')
   "

   echo "All tests completed!"
   EOF

   chmod +x run_tests.sh
   ./run_tests.sh
   ```

**Prevention:** Use consistent development environments and version control

**Related Issues:** [2.3 Python Path Issues](#23-python-path-issues), [6.1 Dependency Installation](#61-dependency-installation)

---

## 7. Emergency Recovery

### Emergency Recovery Procedures

If the application is completely broken and nothing else works:

1. **Quick Recovery (restore to working state):**
   ```bash
   # Navigate to project root
   cd /path/to/MaricopaPropertySearch

   # Restore to last known good state (Phase 3 completion)
   git checkout 41cbaa0

   # Test basic functionality
   python claudedocs/missouri_ave_test.py
   ```

2. **Reset to mock mode (guaranteed working state):**
   ```bash
   python -c "
   from src.enhanced_config_manager import EnhancedConfigManager
   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)
   config.set('api', 'mock_mode', True)
   config.set('gui', 'platform', 'auto')
   print('Configuration reset to safe defaults')
   "

   # Test mock mode
   python claudedocs/missouri_ave_test.py
   ```

3. **Reinstall dependencies:**
   ```bash
   # Clean install
   pip uninstall PyQt5 requests psycopg2 beautifulsoup4 lxml -y

   # System packages (recommended)
   sudo apt update
   sudo apt install python3-pyqt5 python3-requests python3-psycopg2 python3-bs4

   # Test installation
   python -c "import PyQt5; import requests; print('Dependencies OK')"
   ```

4. **Memory-Keeper checkpoint recovery:**
   ```bash
   # If Memory-Keeper is available, restore from checkpoint
   python -c "
   # This would restore from the Phase 3 completion checkpoint
   # if Memory-Keeper integration is available
   print('Checkpoint recovery would restore Phase 3 complete state')
   "
   ```

5. **Complete reinstallation:**
   ```bash
   # Back up current state
   cd ..
   mv MaricopaPropertySearch MaricopaPropertySearch.backup

   # Fresh clone/download
   # git clone <repository> MaricopaPropertySearch
   cd MaricopaPropertySearch

   # Install and test
   pip install -r requirements.txt
   python claudedocs/missouri_ave_test.py
   ```

### Getting Help

1. **Check Phase Completion Documents**: See `checkpoints/` directory for detailed technical information
2. **Run Validation Tests**: Use `claudedocs/missouri_ave_test.py` to verify functionality
3. **Review Memorial Document**: `PHASE_3_COMPLETION_MEMORIAL_2025_09_18.txt` contains complete technical specifications
4. **Check Git History**: All changes documented with commit messages and checkpoints

---

## 📊 Appendices

### Appendix A: Performance Benchmarks

**Expected Performance (Phase 3 Validated):**
- Basic property search: 0.04s average
- Comprehensive data collection: 0.33s average
- Tax history retrieval: 6 records in <1s
- GUI startup: <2 seconds
- Platform detection: <100ms

**Performance Test Command:**
```bash
time python claudedocs/missouri_ave_test.py
```

### Appendix B: Error Code Reference

| Error Pattern | Category | Section |
|---------------|----------|---------|
| `attempted relative import` | Import Issues | [2.1](#21-relative-import-errors) |
| `ModuleNotFoundError` | Import Issues | [2.2](#22-module-not-found-errors) |
| `Display not available` | WSL GUI | [1.1](#11-display-detection-problems) |
| `Qt platform` | WSL GUI | [1.2](#12-platform-detection-failures) |
| `Connection refused` | API/Network | [3.1](#31-api-connection-failures) |
| `Timeout` | API/Network | [3.3](#33-timeout-and-retry-issues) |
| `database is locked` | Database | [4.2](#42-sqlite-fallback-issues) |
| `could not connect to server` | Database | [4.1](#41-postgresql-connection-problems) |

### Appendix C: File References

**Key Configuration Files:**
- `src/enhanced_config_manager.py` - Central configuration
- `src/gui_launcher_unified.py` - Platform detection and GUI launching
- `claudedocs/missouri_ave_test.py` - Comprehensive workflow validation

**Phase Completion Documents:**
- `checkpoints/PHASE_3_GUI_TESTING_COMPLETE_2025_09_18.md`
- `PHASE_3_COMPLETION_MEMORIAL_2025_09_18.txt`
- `MIGRATION_GUIDE.md`

---

**Troubleshooting Guide Version**: Phase 3 Complete (2025-09-18)
**Status**: Validated with Missouri Avenue workflow
**Architecture**: Unified consolidated components
**Platforms**: WSL, Linux, Windows supported

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>