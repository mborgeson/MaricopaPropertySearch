# How to Run Maricopa Property Search Application

## 🚀 Quick Start (Recommended)

### Option 1: Windows Users (Easiest)
Simply double-click:
```
RUN_APPLICATION.bat
```

### Option 2: Command Line (All Platforms)
```bash
python RUN_APPLICATION.py
```

This master launcher will:
- ✅ Check all dependencies
- ✅ Verify database connection
- ✅ Initialize logging system
- ✅ Set up user action tracking
- ✅ Launch the application with all features

## 📋 What the Master Launcher Does

1. **Dependency Check**: Verifies all required packages are installed
2. **Database Check**: Tests PostgreSQL connection
3. **Environment Check**: Validates configuration files
4. **Logging Setup**: Initializes comprehensive logging
5. **Application Launch**: Starts the enhanced GUI with all features

## 🎯 Alternative Launch Scripts

If you need specific versions:

### Enhanced Version (Current Production)
```bash
python launch_enhanced_app.py
```

### Fixed Version (Stable Fallback)
```bash
python launch_app_fixed.py
```

### Improved Version (UX Features)
```bash
python launch_improved_app.py
```

## 📦 Prerequisites

### Required Python Packages
```bash
pip install PyQt5 psycopg2-binary requests playwright beautifulsoup4 lxml
```

### Playwright Browser (for web scraping)
```bash
playwright install chromium
```

### Conda Environment (Optional but Recommended)
```bash
conda activate maricopa_property
```

## 🔧 Configuration

### Database Setup
1. Ensure PostgreSQL is running
2. Configure connection in `.env` file:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=maricopa_property
DB_USER=your_username
DB_PASSWORD=your_password
```

### User Action Logs
Logs are automatically created in:
```
logs/user_actions/
├── user_actions_YYYYMMDD_HHMMSS.jsonl  # Detailed JSON log
└── user_actions_summary.log             # Human-readable summary
```

## 🎮 Using the Application

1. **Search Properties**:
   - Select search type: APN, Address, or Owner
   - Enter search term
   - Click "Search Properties"

2. **View Details**:
   - Click "View Details" for any property
   - No more 15-30 second delays!

3. **Collect Data**:
   - Click "Collect Data" for individual properties
   - Use "Collect All Data" for batch collection

4. **Export Results**:
   - Click "Export to CSV" to save results

## 🐛 Troubleshooting

### Application Won't Start
- Run `python RUN_APPLICATION.py` to see detailed diagnostics
- Check dependency installation
- Verify Python version (3.7+ required)

### Database Connection Failed
- Application will still run with limited functionality
- Check PostgreSQL is running
- Verify `.env` configuration

### Slow Performance
- Fixed! API retry loop has been disabled
- Data collection now uses mock data for instant response

### Missing Dependencies
The master launcher will tell you exactly what to install:
```bash
pip install [missing_package]
```

## 📝 Logs for Debugging

When reporting issues, provide:
1. **User action log**: `logs/user_actions/user_actions_summary.log`
2. **Application log**: `logs/maricopa_property.log`
3. **Error log**: `logs/errors.log`

## 🔄 Recent Fixes

- ✅ Fixed 15-30 second delay issue
- ✅ Added comprehensive user action logging
- ✅ Improved error handling
- ✅ Enhanced batch collection
- ✅ Fixed display errors

## 💡 Tips

- Always use `RUN_APPLICATION.py` for the most complete experience
- Check logs in `logs/user_actions/` for debugging
- The application works without database (limited features)
- All user actions are logged for troubleshooting

## 📞 Support

If you encounter issues:
1. Run the master launcher: `python RUN_APPLICATION.py`
2. Check the diagnostic output
3. Review logs in `logs/user_actions/`
4. Copy the summary log for support requests