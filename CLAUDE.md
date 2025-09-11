# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Maricopa County Property Search Tool - A Python tkinter application for searching and managing property information from Maricopa County Assessor's office. The application supports multiple data sources including web scraping, CSV imports, and API integration.

## Running the Application

```bash
# Run the main application
python maricopa_property_search.py
```

## Dependencies

### Required
- Python 3.x
- tkinter (included with Python)
- requests

### Optional (for enhanced functionality)
```bash
# For web scraping capabilities
pip install beautifulsoup4 lxml
```

## Architecture

### Data Sources
The application uses a multi-source approach for property data:

1. **API Integration** (APIConfig class, lines 39-69)
   - Base URL: https://mcassessor.maricopa.gov
   - Configurable endpoints for parcels, property, search
   - Headers include User-Agent and authentication support

2. **Web Scraping** (MaricopaScraper class, lines 160-250)
   - Fallback when API unavailable
   - BeautifulSoup-based HTML parsing
   - Parcel viewer URL scraping

3. **CSV Import** (CSVImporter class, lines 254-321)
   - Bulk data import capability
   - Flexible column mapping
   - Cache storage for offline access

### Core Components

**Data Models** (lines 75-154)
- `PropertyInfo`: Main property data structure with CSV export
- `TaxInfo`: Tax assessment information
- `SaleInfo`: Sales history records

**MaricopaAssessorAPI** (lines 327-541)
- Central API client with retry logic
- Manages all data sources (API, scraping, CSV)
- Caching system for imported data
- Fallback to mock data when sources unavailable

**PropertySearchApp** (lines 608-1123)
- Main GUI application using tkinter
- Multi-tab interface (Property, Tax, Sales, Documents, API Help)
- Background threading for non-blocking searches
- Export functionality to CSV

### Key Features

- **Multiple Search Methods**: APN, address, batch file, CSV import
- **Data Source Selection**: Toggle between API, web scraping, and CSV cache
- **Export Capabilities**: Save property data to CSV files
- **Document Links**: Direct links to assessor, recorder, and tax bill websites
- **API Discovery Helper**: Instructions for finding real API endpoints (APIEndpointFinder class)

## API Configuration

To use real data instead of mock data:

1. Update `APIConfig` class (lines 39-69) with actual endpoints from Maricopa County
2. Use the API Help tab in the application for instructions on finding endpoints via browser DevTools
3. Add API key if required: `API_KEY = "your-key-here"`

## Data Flow

1. User enters search criteria (APN/address)
2. Application checks data sources in order:
   - CSV cache (if imported)
   - API endpoints (if configured)
   - Web scraping (if beautifulsoup4 installed)
   - Mock data (fallback)
3. Results displayed in tabbed interface
4. Additional data (tax, sales) loaded asynchronously
5. Export options available for all data

## Important URLs

- Assessor Parcel Viewer: https://mcassessor.maricopa.gov/parcel/{apn}
- Recorder Documents: https://recorder.maricopa.gov/recdocdata/
- Tax Information: https://treasurer.maricopa.gov/parcelinfo/

## Testing with Mock Data

The application includes comprehensive mock data generation when real sources are unavailable. This allows testing of the full UI and workflow without API access.