# API Configuration Guide

## Overview

The Maricopa Property Search application supports multiple data sources for property information. This guide covers the configuration and usage of all available APIs and data sources.

## Data Source Priority

The application uses multiple data sources in priority order:

1. **API** (Fastest, requires authentication)
2. **Web Scraping** (Reliable, moderate speed)
3. **Database Cache** (Fastest for repeat queries)

## Maricopa County API Configuration

### Getting API Access

1. **Visit Maricopa County Assessor Website**
   - URL: https://mcassessor.maricopa.gov
   - Navigate to Developer/API section
   - Request developer access

2. **API Registration Process**
   - Complete developer application
   - Provide application details and use case
   - Wait for approval (typically 3-5 business days)
   - Receive API token via email

3. **API Documentation**
   - Base URL: `https://mcassessor.maricopa.gov/api`
   - Authentication: Token-based
   - Rate Limits: 1000 requests per hour (default)

### Configuration Setup

#### Method 1: Configuration File

Edit `config/config.ini`:

```ini
[api]
base_url = https://mcassessor.maricopa.gov
token = your_api_token_here
timeout = 30
max_retries = 3
rate_limit = 10
```

#### Method 2: Environment Variables

Edit `.env` file:

```bash
API_TOKEN=your_api_token_here
API_BASE_URL=https://mcassessor.maricopa.gov
API_TIMEOUT=30
API_MAX_RETRIES=3
API_RATE_LIMIT=10
```

#### Method 3: GUI Settings

1. Launch application
2. Go to Settings → Data Sources
3. Enter API token
4. Test connection
5. Save configuration

### Available API Endpoints

#### Property Search Endpoint

```
GET /api/v1/properties/search
```

**Parameters**:
- `q` (string): Search query (address, owner, APN)
- `type` (string): Search type (address, owner, apn)
- `limit` (integer): Maximum results (default: 20)
- `offset` (integer): Result offset for pagination

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "apn": "123-45-678",
      "address": "10000 W Missouri Ave, Phoenix, AZ",
      "owner_name": "John Doe",
      "property_type": "Residential",
      "market_value": 350000,
      "assessed_value": 280000,
      "square_feet": 2100,
      "year_built": 2005
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```

#### Property Details Endpoint

```
GET /api/v1/properties/{apn}
```

**Parameters**:
- `apn` (string): Assessor's Parcel Number

**Response**:
```json
{
  "status": "success",
  "data": {
    "apn": "123-45-678",
    "address": "10000 W Missouri Ave, Phoenix, AZ",
    "owner_name": "John Doe",
    "property_type": "Residential",
    "market_value": 350000,
    "assessed_value": 280000,
    "square_feet": 2100,
    "lot_size": 0.25,
    "year_built": 2005,
    "bedrooms": 4,
    "bathrooms": 2.5,
    "legal_description": "LOT 1 BLOCK 2 EXAMPLE SUBDIVISION",
    "zoning": "R1-6",
    "use_code": "SINGLE FAMILY"
  }
}
```

#### Tax History Endpoint

```
GET /api/v1/properties/{apn}/tax-history
```

**Parameters**:
- `apn` (string): Assessor's Parcel Number
- `years` (integer): Number of years to retrieve (default: 5)

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "tax_year": 2024,
      "assessed_value": 280000,
      "full_cash_value": 350000,
      "tax_amount": 3456.78,
      "payment_status": "Paid",
      "due_date": "2024-10-01",
      "paid_date": "2024-09-15"
    }
  ]
}
```

#### Sales History Endpoint

```
GET /api/v1/properties/{apn}/sales-history
```

**Parameters**:
- `apn` (string): Assessor's Parcel Number
- `years` (integer): Number of years to retrieve (default: 10)

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "sale_date": "2023-03-15",
      "sale_price": 325000,
      "buyer": "John Doe",
      "seller": "Jane Smith",
      "document_number": "2023-0123456",
      "sale_type": "Warranty Deed"
    }
  ]
}
```

### Authentication

#### Token-Based Authentication

All API requests require authentication via token:

```bash
# Header format
Authorization: Bearer your_api_token_here

# Example curl request
curl -H "Authorization: Bearer your_api_token_here" \
     "https://mcassessor.maricopa.gov/api/v1/properties/search?q=10000%20W%20Missouri%20Ave"
```

#### Token Management

**Token Expiration**:
- Standard tokens: 1 year validity
- Refresh before expiration
- Application will show warning 30 days before expiration

**Token Security**:
- Store tokens securely (not in code)
- Use environment variables or secure configuration
- Rotate tokens regularly
- Monitor token usage

### Rate Limiting

#### Default Limits

- **Free Tier**: 1,000 requests per hour
- **Premium Tier**: 10,000 requests per hour
- **Enterprise Tier**: 100,000 requests per hour

#### Rate Limit Handling

The application automatically handles rate limits:

```python
# Automatic retry with exponential backoff
# Rate limit exceeded → Wait and retry
# Multiple failures → Switch to web scraping
```

#### Configuration

```ini
[api]
rate_limit = 10           # Requests per second
max_retries = 3          # Retry attempts
retry_delay = 5          # Initial delay (seconds)
backoff_factor = 2       # Exponential backoff multiplier
```

### Error Handling

#### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Unauthorized | Check API token |
| 403 | Forbidden | Verify permissions |
| 429 | Rate Limited | Reduce request frequency |
| 500 | Server Error | Retry later |
| 503 | Service Unavailable | Check system status |

#### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": 401,
    "message": "Invalid API token",
    "details": "Token has expired or is invalid"
  }
}
```

#### Application Error Handling

- **Automatic Fallback**: Switch to web scraping on API failures
- **User Notifications**: Clear error messages with solutions
- **Retry Logic**: Intelligent retry with exponential backoff
- **Status Reporting**: Real-time status in application interface

## Web Scraping Configuration

### Browser Setup

#### Supported Browsers

1. **Chrome/Chromium** (Recommended)
   - Better performance
   - More stable
   - Better JavaScript support

2. **Firefox**
   - Alternative option
   - Good for specific sites
   - Privacy-focused

#### Installation

```bash
# Install browser automation
playwright install chromium

# Or use the provided script
python scripts/install_chromedriver.py
```

#### Configuration

```ini
[scraping]
browser = chrome
headless = true
timeout = 30
max_workers = 5
screenshot_on_error = true
parallel_browsers = 3
```

### Scraping Targets

#### Maricopa County Assessor

**Property Search**:
- URL: `https://mcassessor.maricopa.gov/parcel/`
- Search Types: APN, Address, Owner
- Data Extracted: Basic property info, assessment details

**Property Details**:
- URL: `https://mcassessor.maricopa.gov/parcel/{apn}`
- Data Extracted: Complete property characteristics
- Images: Property photos (if available)

#### Maricopa County Recorder

**Document Search**:
- URL: `https://recorder.maricopa.gov/recdocdata/`
- Search by: APN, Document Number, Date Range
- Data Extracted: Recorded documents, deeds, mortgages

#### Maricopa County Treasurer

**Tax Information**:
- URL: `https://treasurer.maricopa.gov/parcelinfo/`
- Search by: APN
- Data Extracted: Tax bills, payment history, delinquency status

### Performance Optimization

#### Concurrent Processing

```ini
[scraping]
max_workers = 5          # Concurrent browser instances
parallel_browsers = 3    # Simultaneous page loads
batch_size = 10         # Properties per batch
```

#### Caching Strategy

```ini
[caching]
enable_page_cache = true
cache_timeout = 3600    # 1 hour
max_cache_size = 1000   # Number of cached pages
```

#### Resource Management

```ini
[resources]
memory_limit = 2048     # MB per browser
cpu_limit = 80          # Max CPU usage %
disk_cache = 512        # MB disk cache
```

## Database Cache Configuration

### Cache Strategy

#### Primary Database

- **Purpose**: Persistent storage for collected data
- **Technology**: PostgreSQL
- **Retention**: Permanent (with cleanup)

#### Cache Database

- **Purpose**: Fast access to recent searches
- **Technology**: SQLite (local) or Redis (distributed)
- **Retention**: 24 hours (configurable)

### Cache Configuration

```ini
[cache]
enable_cache = true
cache_type = database    # database, memory, redis
cache_timeout = 86400   # 24 hours in seconds
max_cache_size = 10000  # Maximum cached properties
cleanup_interval = 3600 # Cache cleanup every hour
```

### Cache Management

#### Automatic Cache Updates

- **Fresh Data**: Cache updated when new data collected
- **Expiration**: Automatic expiration based on age
- **Validation**: Data freshness checks before serving

#### Manual Cache Control

```python
# Clear specific property cache
cache.clear_property('123-45-678')

# Clear all cache
cache.clear_all()

# Refresh specific property
cache.refresh_property('123-45-678')
```

#### Cache Performance

```sql
-- Cache hit rate monitoring
SELECT
    cache_hits,
    cache_misses,
    (cache_hits::float / (cache_hits + cache_misses)) * 100 as hit_rate
FROM cache_statistics;
```

## Testing and Validation

### API Testing

#### Manual Testing

```bash
# Test API connectivity
python scripts/test_real_endpoints.py

# Test specific endpoint
curl -H "Authorization: Bearer your_token" \
     "https://mcassessor.maricopa.gov/api/v1/properties/search?q=test"
```

#### Automated Testing

```python
# Run API tests
pytest tests/test_api_client.py

# Test with different scenarios
pytest tests/test_api_integration.py -v
```

### Web Scraping Testing

```bash
# Test browser setup
python scripts/test_browser_setup.py

# Test specific scraping targets
python scripts/test_scraping_endpoints.py
```

### Cache Testing

```bash
# Test database connectivity
python scripts/test_db_connection.py

# Test cache performance
python scripts/test_cache_performance.py
```

### Integration Testing

```bash
# Test all data sources
python scripts/test_all_sources.py

# Performance testing
python scripts/test_performance.py
```

## Monitoring and Maintenance

### Performance Monitoring

#### API Metrics

- **Response Times**: Average API response time
- **Success Rate**: Percentage of successful API calls
- **Rate Limit Usage**: Current rate limit utilization
- **Error Frequency**: API error frequency and types

#### Scraping Metrics

- **Page Load Times**: Browser automation performance
- **Success Rate**: Successful data extraction rate
- **Resource Usage**: CPU and memory consumption
- **Error Frequency**: Scraping failure rate and causes

#### Cache Metrics

- **Hit Rate**: Cache hit vs. miss ratio
- **Memory Usage**: Cache memory consumption
- **Database Performance**: Query response times
- **Storage Usage**: Disk space utilization

### Health Monitoring

#### Automated Checks

```bash
# Daily health check
python scripts/daily_health_check.py

# Real-time monitoring
python scripts/monitor_sources.py
```

#### Alert Configuration

```ini
[monitoring]
enable_alerts = true
api_failure_threshold = 5      # Failures before alert
scraping_failure_threshold = 3 # Failures before alert
response_time_threshold = 10   # Seconds
email_alerts = admin@company.com
```

### Maintenance Tasks

#### Daily Tasks

```bash
# Clear expired cache
python scripts/cleanup_cache.py

# Update database statistics
python scripts/update_db_stats.py

# Generate performance report
python scripts/daily_report.py
```

#### Weekly Tasks

```bash
# Database maintenance
python scripts/database_maintenance.py

# Clean log files
python scripts/cleanup_logs.py

# Update browser drivers
playwright install chromium --force
```

#### Monthly Tasks

```bash
# Full system backup
python scripts/backup_system.py

# Performance optimization
python scripts/optimize_database.py

# Security audit
python scripts/security_audit.py
```

## Best Practices

### API Usage

1. **Token Security**
   - Store tokens in environment variables
   - Rotate tokens regularly
   - Monitor token usage

2. **Rate Limit Management**
   - Implement exponential backoff
   - Cache responses when possible
   - Use batch requests when available

3. **Error Handling**
   - Implement comprehensive error handling
   - Provide fallback mechanisms
   - Log errors for analysis

### Web Scraping

1. **Respectful Scraping**
   - Follow robots.txt
   - Implement delays between requests
   - Monitor resource usage

2. **Reliability**
   - Handle dynamic content
   - Implement retry logic
   - Use multiple selectors

3. **Maintenance**
   - Monitor for website changes
   - Update selectors regularly
   - Test scraping logic frequently

### Database Management

1. **Performance**
   - Use appropriate indexes
   - Regular database maintenance
   - Monitor query performance

2. **Data Quality**
   - Validate data before storage
   - Implement data cleanup routines
   - Monitor data consistency

3. **Backup and Recovery**
   - Regular automated backups
   - Test restore procedures
   - Monitor backup integrity

## Troubleshooting

### Common API Issues

**Problem**: API authentication failed
**Solution**:
1. Verify token in configuration
2. Check token expiration
3. Test token with curl
4. Contact API provider

**Problem**: Rate limit exceeded
**Solution**:
1. Reduce request frequency
2. Implement request queuing
3. Consider upgrading API tier
4. Use caching more aggressively

### Common Scraping Issues

**Problem**: Browser automation failed
**Solution**:
1. Update browser drivers
2. Check browser installation
3. Verify website accessibility
4. Review scraping selectors

**Problem**: Data extraction failed
**Solution**:
1. Check website changes
2. Update CSS selectors
3. Handle dynamic content
4. Implement fallback methods

### Common Cache Issues

**Problem**: Cache not working
**Solution**:
1. Check database connectivity
2. Verify cache configuration
3. Monitor cache statistics
4. Clear corrupted cache

**Problem**: Poor cache performance
**Solution**:
1. Optimize database queries
2. Adjust cache size limits
3. Update database statistics
4. Consider cache partitioning

---

**Last Updated**: January 2025
**Version**: 2.0
**Status**: Production Ready

This guide provides comprehensive information for configuring and managing all data sources in the Maricopa Property Search application.