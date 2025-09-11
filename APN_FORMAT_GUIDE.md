# Maricopa County APN Format Guide

## Proper APN Format

Maricopa County Assessor Parcel Numbers (APNs) follow this format:
- **Standard Format**: `XXX-XX-XXX` (e.g., 501-38-237)
- **With Letter Suffix**: `XXX-XX-XXXA` (e.g., 211-29-043A)
- **Extended Format**: `XXX-XX-XXXX` (some parcels have 4 digits in the last segment)

### Examples of Valid APNs:
- `501-38-237`
- `134-24-001`
- `211-29-043`
- `162-09-032A`
- `112-47-1234`

## How to Enter APNs in the Application

The application accepts APNs in multiple formats:
1. **With dashes** (preferred): `501-38-237`
2. **With spaces**: `501 38 237`
3. **No separators**: `50138237`
4. **Mixed case**: The application automatically converts to uppercase

## Current Status

### Working Features:
✅ CSV Import - Load property data from CSV files
✅ Multiple APN format support
✅ Address search capability
✅ Export to CSV
✅ Links to assessor website

### Known Issues:
❌ **Web Scraping**: The Maricopa County website structure has changed or blocks automated scraping
❌ **API Access**: Requires authentication tokens not publicly available
❌ **Direct Property Lookup**: The /parcel/ URLs return 500 errors

## Troubleshooting

### No Results Found?
1. **Verify APN Format**: Ensure you're using the correct format (XXX-XX-XXX)
2. **Check County**: Confirm the property is in Maricopa County
3. **Use CSV Import**: If you have property data in CSV format, import it first
4. **Manual Search**: Visit https://mcassessor.maricopa.gov and search manually

### To Get Real Data:
1. **Option 1**: Export data from the Maricopa County website manually and import as CSV
2. **Option 2**: Contact Maricopa County for API access token
3. **Option 3**: Use the website's search function directly

## CSV Import Format

If importing property data via CSV, use these column headers:
- `APN` or `Parcel`
- `Owner` or `owner_name`
- `Property Address` or `situs_address`
- `Mailing Address` or `mail_address`
- `Assessed Value` or `assessed_value`
- `Market Value` or `market_value`

## Contact Information

For API access or technical questions:
- **Phone**: 602-506-3406
- **Website**: https://mcassessor.maricopa.gov
- **API Request**: Use the contact form and select "API Question/Token"