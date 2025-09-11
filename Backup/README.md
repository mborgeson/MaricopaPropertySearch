# Maricopa County Property Search Tool

A Python application for searching and managing property information from Maricopa County Assessor's Office.

## Features

- **Property Search**: Search by APN (Assessor Parcel Number) or address
- **Web Scraping**: Extracts property data from the county website (when available)
- **CSV Import/Export**: Import bulk property data and export results
- **Batch Processing**: Process multiple APNs from a file
- **Tax Information**: View property tax details
- **Sales History**: Access property sales records
- **Direct Links**: Open properties on the official assessor website

## Installation

### Requirements
- Python 3.x (with tkinter)
- Required packages:
  ```bash
  pip install requests
  ```

### Optional (for enhanced web scraping)
```bash
pip install beautifulsoup4 lxml
```

## Usage

### Running the Application
```bash
python maricopa_property_search.py
```

### Search Options

1. **By Address** (default): Enter a property address like "4317 E Calle Feliz"
2. **By APN**: Enter an APN like "501-38-237"
3. **Import CSV**: Load property data from a CSV file

### Data Sources

The application uses multiple data sources in order of priority:
1. **CSV Cache**: Previously imported property data
2. **Web Scraping**: Live data from mcassessor.maricopa.gov (requires beautifulsoup4)
3. **Mock Data**: Sample data for testing when real data isn't available

## API Status

The Maricopa County Assessor's API documented in their PDF requires special authentication tokens that are not publicly available. The API endpoints return 500 errors without proper authentication. 

This application has been updated to work without API tokens by using:
- Web scraping for real-time data (when beautifulsoup4 is installed)
- CSV import for bulk data processing
- Mock data for testing and demonstration

## Testing

The application has been tested with the address "4317 E Calle Feliz" and successfully:
- Launches the GUI interface
- Accepts search input
- Returns property information (mock data when scraping unavailable)
- Exports results to CSV
- Opens links to the assessor website

## Current Limitations

1. **API Access**: The documented API endpoints are not publicly accessible without authentication
2. **Web Scraping**: Results depend on the website's HTML structure which may change
3. **Real-time Data**: Without API access, real-time property data requires web scraping

## Future Improvements

If you obtain an API token from Maricopa County:
1. The code structure is already in place to support API integration
2. Simply update the `APIConfig` class with your token
3. The application will automatically use API endpoints when available

## Files

- `maricopa_property_search.py` - Main application file
- `MC-Assessor-API-Documentation.pdf` - Official API documentation (requires token)
- `CLAUDE.md` - Development guidance for Claude AI
- `README.md` - This file

## Support

For API access, contact Maricopa County Assessor's Office through their website and select "API Question/Token" as the subject.