# Platform Compatibility Guide

## Overview

The Maricopa Property Search application now uses a unified smart launcher (`RUN_APPLICATION.py`) that automatically detects your environment and adapts accordingly. This guide explains the different environments and troubleshooting steps.

## Supported Platforms

### ✅ Windows Native
- **Status**: Fully supported
- **Qt Platform**: `windows`
- **Display**: Native Windows display system
- **Features**: All features available

### ✅ WSL with X Server
- **Status**: Fully supported with X server
- **Qt Platform**: `xcb` (X11)
- **Display**: X server forwarding required
- **Features**: All features available

### ✅ WSL Headless
- **Status**: Supported in test mode
- **Qt Platform**: `offscreen`
- **Display**: No GUI display (testing only)
- **Features**: Backend functionality, no visual interface

### ✅ Linux Native
- **Status**: Fully supported
- **Qt Platform**: `xcb` (X11)
- **Display**: Native X11 display
- **Features**: All features available

## Environment Detection

The launcher automatically detects:

1. **Platform Type**: Windows, Linux, or WSL
2. **Display Availability**: Whether GUI can be displayed
3. **Qt Compatibility**: Best Qt platform plugin to use
4. **Dependencies**: Available and missing packages

## Automatic Adaptations

### Qt Platform Selection
```
Windows Native  → QT_QPA_PLATFORM=windows
Linux + Display → QT_QPA_PLATFORM=xcb
WSL + Display   → QT_QPA_PLATFORM=xcb
No Display      → QT_QPA_PLATFORM=offscreen
```

### Launch Strategies
The launcher tries multiple strategies in order:
1. **Enhanced GUI**: Full application with all features
2. **Basic GUI**: Simplified interface with core features
3. **Minimal GUI**: Test interface for compatibility checking
4. **Console Mode**: Text-based interface (future feature)

## Common Issues and Solutions

### Qt Plugin Errors

#### Error: "qt.qpa.plugin: Could not load the Qt platform plugin 'xcb'"
**Solution**: The launcher will automatically switch to offscreen mode.

**Manual Fix**:
```bash
export QT_QPA_PLATFORM=offscreen
python3 RUN_APPLICATION.py
```

#### Error: "qt.qpa.xcb: could not connect to display"
**Cause**: No X server available in WSL

**Solutions**:
1. **Install X Server (Recommended)**:
   - Windows: Install VcXsrv or Xming
   - Start X server with: `export DISPLAY=:0`

2. **Use Headless Mode**:
   ```bash
   export QT_QPA_PLATFORM=offscreen
   python3 RUN_APPLICATION.py
   ```

### WSL Display Issues

#### Setting up X Server in WSL
1. **Install X Server on Windows**:
   - Download VcXsrv: https://sourceforge.net/projects/vcxsrv/
   - Or Xming: https://sourceforge.net/projects/xming/

2. **Configure X Server**:
   - Start with settings: "Multiple windows", "Start no client", "Disable access control"

3. **Set DISPLAY in WSL**:
   ```bash
   export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0.0
   # Or simply:
   export DISPLAY=:0
   ```

4. **Test X11 forwarding**:
   ```bash
   sudo apt install x11-apps
   xclock  # Should show a clock window
   ```

### Path Issues

The launcher handles path differences automatically:
- **Windows**: Uses backslashes and Windows paths
- **WSL**: Converts Windows paths to WSL paths
- **Linux**: Uses forward slashes and Unix paths

### Dependency Issues

#### Missing PyQt5
```bash
# Ubuntu/Debian
sudo apt install python3-pyqt5

# Or with pip
pip install PyQt5
```

#### Missing Database Dependencies
```bash
# For PostgreSQL support
sudo apt install python3-psycopg2
# Or
pip install psycopg2-binary
```

## Environment Variables

### Manual Control
You can override automatic detection:

```bash
# Force offscreen mode
export QT_QPA_PLATFORM=offscreen

# Force X11 mode
export QT_QPA_PLATFORM=xcb

# Set custom display
export DISPLAY=:0

# Debug Qt plugins
export QT_DEBUG_PLUGINS=1
```

### Debugging
```bash
# Enable Qt logging
export QT_LOGGING_RULES="*.debug=true"

# Show Qt platform info
export QT_QPA_PLATFORM_PLUGIN_PATH=""
```

## Testing Your Environment

### Quick Test
```bash
python3 RUN_APPLICATION.py
```

The launcher will show detailed information about:
- Platform detection results
- Available dependencies
- Display capabilities
- Qt platform selection

### Manual Platform Check
```python
import platform
import os
from pathlib import Path

# Check platform
print(f"System: {platform.system()}")
print(f"Release: {platform.release()}")

# Check WSL
is_wsl = 'microsoft' in platform.release().lower()
print(f"WSL: {is_wsl}")

# Check display
print(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
```

## Performance Considerations

### Windows Native
- **Best Performance**: Native Windows GUI
- **Startup Time**: ~2-3 seconds
- **Memory Usage**: ~50-100MB

### WSL with X Server
- **Good Performance**: X11 forwarding overhead
- **Startup Time**: ~3-5 seconds
- **Memory Usage**: ~70-120MB

### WSL Headless
- **Excellent Performance**: No GUI overhead
- **Startup Time**: ~1-2 seconds
- **Memory Usage**: ~30-50MB

## Troubleshooting Steps

### Step 1: Check Environment
```bash
python3 RUN_APPLICATION.py
# Look at the "Platform Detection" section
```

### Step 2: Verify Dependencies
```bash
python3 -c "import PyQt5; print('PyQt5 OK')"
python3 -c "import requests; print('requests OK')"
```

### Step 3: Test Display (Linux/WSL)
```bash
echo $DISPLAY
xset q  # Should show X server info
```

### Step 4: Force Offscreen Mode
```bash
export QT_QPA_PLATFORM=offscreen
python3 RUN_APPLICATION.py
```

### Step 5: Check Logs
```bash
# Application logs
tail -f logs/app.log

# System logs (Linux)
journalctl -f
```

## Advanced Configuration

### Custom Qt Platform Plugin Path
```bash
export QT_QPA_PLATFORM_PLUGIN_PATH="/custom/path/to/qt/plugins"
```

### Custom DPI Settings
```bash
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_SCALE_FACTOR=1.5
```

### Memory Optimization
```bash
export QT_QUICK_CONTROLS_STYLE=Basic
export QT_QUICK_CONTROLS_MATERIAL_THEME=Light
```

## Support

For platform-specific issues:

1. **Check this guide** for common solutions
2. **Run diagnostics**: `python3 RUN_APPLICATION.py` shows detailed environment info
3. **Check logs**: Application logs in `logs/` directory
4. **Test in offscreen mode**: Always works for testing backend functionality

## Future Enhancements

Planned improvements:
- **Console Mode**: Text-based interface for headless servers
- **Web Interface**: Browser-based GUI for remote access
- **Docker Support**: Containerized deployment
- **Auto X-Server**: Automatic X server setup for WSL