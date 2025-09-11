# 🚀 Quick Start Guide

## Prerequisites Fixed ✅
- Missing dependency `psycopg2-binary` has been installed
- PyQt5 signal connection issue has been resolved
- Application is now fully operational

## Launch Application

### Method 1: Batch File (Easiest)
```batch
launch_app.bat
```

### Method 2: Direct Python
```bash
python "src\maricopa_property_search.py"
```

### Method 3: With Dependencies Check
```bash
pip install -r requirements.txt
python "src\maricopa_property_search.py"
```

## Application Interface

When launched, you'll see:

1. **Search Section** (Top)
   - Dropdown: Choose "Owner Name", "Property Address", or "APN"
   - Input Field: Enter your search term
   - Search Button: Execute search

2. **Results Table** (Bottom)
   - Shows: APN, Owner, Address, Year Built, Living Area, Assessed Value
   - Double-click any row for detailed property information
   - Export results to CSV using the "Export Results" button

## Sample Searches (Mock Data)

Try these searches to test the system:

- **Owner Name**: "Smith" or "Johnson"
- **Property Address**: "Main Street" or "Oak Avenue" 
- **APN**: "12345001" or "67890001"

The system will generate sample data for demonstration.

## Database Status

- **Database**: maricopa_properties (PostgreSQL)
- **Connection**: localhost:5433
- **Status**: ✅ Connected and operational
- **Tables**: 6 tables created with indexes

## Troubleshooting

### If dependencies are missing:
```bash
pip install psycopg2-binary PyQt5 selenium requests python-dotenv
```

### If PostgreSQL connection fails:
- Ensure PostgreSQL service is running
- Verify port 5433 is accessible
- Check database credentials in `.env` file

### If GUI doesn't appear:
- Check Python environment is activated
- Verify PyQt5 is properly installed
- Try running from command line to see error messages

---

**🎉 Your application is ready! Launch it now with `launch_app.bat`**