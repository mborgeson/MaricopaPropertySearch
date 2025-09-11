# Background Data Collection System

## Overview

The Background Data Collection System transforms the manual "Collect Complete Property Data" process into an intelligent, non-blocking automation system. This system automatically enhances search results by collecting tax and sales data in the background without freezing the user interface.

## Key Features

### 🔄 Automatic Background Enhancement
- **Search Result Enhancement**: Automatically queues top search results for data collection
- **Intelligent Prioritization**: High priority for user-viewed properties, normal priority for bulk operations
- **Smart Caching**: Avoids duplicate collection with 24-hour data freshness validation
- **Non-blocking UI**: All data collection happens in background threads

### ⚡ High-Performance Architecture
- **Concurrent Processing**: Configurable concurrent job execution (default: 3 simultaneous)
- **Thread-Safe Database**: Connection pooling optimized for concurrent operations
- **Queue Management**: Priority-based job queue with retry logic and error handling
- **Memory Efficient**: Smart caching with automatic cleanup of expired entries

### 📊 Real-Time Progress Tracking
- **Live Status Updates**: Real-time display of pending, active, and completed jobs
- **Success Rate Monitoring**: Track collection success rates and performance metrics
- **Progress Visualization**: Visual indicators for data collection status in search results
- **Error Handling**: Graceful error recovery with exponential backoff retry logic

### 🎯 User Experience Enhancements
- **Instant Search Results**: Show basic property info immediately
- **Progressive Enhancement**: Data appears as it becomes available
- **Manual Override**: Users can still trigger immediate data collection when needed
- **Status Transparency**: Clear indication of data completeness for each property

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Enhanced Main Window                     │
├─────────────────────────────────────────────────────────────┤
│  Search Input → Results Table → Background Status Panel    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│  Background Data Collection Manager                         │
├─────────────────────┼───────────────────────────────────────┤
│  • Job Prioritization                                       │
│  • Cache Management                                         │
│  • Progress Tracking                                        │
│  • Signal Coordination                                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│  Background Data Worker (QThread)                          │
├─────────────────────┼───────────────────────────────────────┤
│  • Priority Queue Processing                               │
│  • Concurrent Job Execution                                │
│  • Retry Logic & Error Handling                            │
│  • Performance Statistics                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│  Thread-Safe Database Manager                              │
├─────────────────────┼───────────────────────────────────────┤
│  • Connection Pool (5-20 connections)                      │
│  • Concurrent-Safe Operations                              │
│  • Bulk Insert Optimization                                │
│  • Performance Monitoring                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│  Automatic Data Collector                                  │
├─────────────────────┼───────────────────────────────────────┤
│  • Playwright Web Scraping                                 │
│  • Tax Data Collection                                     │
│  • Sales Data Collection                                   │
│  • Data Validation & Storage                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### BackgroundDataCollectionManager
**Location**: `src/background_data_collector.py`
- **Purpose**: High-level manager coordinating all background collection activities
- **Key Methods**:
  - `start_collection()`: Initializes background worker thread
  - `enhance_search_results()`: Queues search results for automatic enhancement
  - `collect_data_for_apn()`: Request immediate collection for specific property

### BackgroundDataWorker (QThread)
**Location**: `src/background_data_collector.py`
- **Purpose**: Background thread executing data collection jobs
- **Features**:
  - Priority queue processing with JobPriority (CRITICAL, HIGH, NORMAL, LOW)
  - Concurrent job execution using ThreadPoolExecutor
  - Automatic retry with exponential backoff
  - Real-time progress reporting via Qt signals

### ThreadSafeDatabaseManager
**Location**: `src/threadsafe_database_manager.py`
- **Purpose**: Thread-safe database operations optimized for concurrent access
- **Features**:
  - Connection pooling (5-20 connections)
  - Upsert operations preventing duplicate data conflicts
  - Bulk insert optimization for better performance
  - Operation statistics tracking

### Enhanced Main Window
**Location**: `src/gui/enhanced_main_window.py`
- **Purpose**: UI integration with background collection system
- **Features**:
  - Background status panel with start/stop controls
  - Real-time progress updates in search results table
  - Enhanced property details dialog with collection options
  - Collection statistics and performance monitoring

## Installation & Setup

### 1. Dependencies
```bash
# Install required Python packages
pip install PyQt5 psycopg2-binary playwright asyncio

# Install Playwright browsers
playwright install chromium
```

### 2. Database Setup
The system requires PostgreSQL with the existing schema plus additional tables:
```sql
-- Data collection status tracking
CREATE TABLE data_collection_status (
    apn VARCHAR(50) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_collection_status_status ON data_collection_status(status);
CREATE INDEX idx_collection_status_completed ON data_collection_status(completed_at) WHERE status = 'completed';
```

### 3. Configuration
Create or update `config.json` with enhanced settings:
```json
{
  "background_collection": {
    "max_concurrent_jobs": 3,
    "job_timeout_seconds": 300,
    "retry_attempts": 3,
    "cache_expiry_hours": 24,
    "auto_start_collection": true
  },
  "database_pool": {
    "min_connections": 5,
    "max_connections": 20,
    "connection_timeout_seconds": 30
  },
  "performance": {
    "enable_performance_monitoring": true,
    "log_slow_operations": true,
    "slow_operation_threshold_seconds": 2.0
  }
}
```

### 4. Launch Enhanced Application
```bash
# Launch the enhanced application
python launch_enhanced_app.py
```

## Usage Guide

### Basic Operation
1. **Application Startup**: Background collection starts automatically
2. **Perform Search**: Enter owner name, address, or APN and search
3. **Automatic Enhancement**: Top results are automatically queued for data collection
4. **Progress Monitoring**: Watch the background status panel for progress
5. **View Details**: Click on any property to see detailed information as it becomes available

### Manual Data Collection
For immediate data needs:
1. Select a property in the search results
2. Click "View Details"
3. Use "Auto-Collect Data (Background)" for queued collection
4. Use "Manual Collect (Immediate)" for blocking collection

### Background Collection Controls
- **Start/Stop**: Use the background status panel to control collection
- **Bulk Collection**: Use "Auto-Collect All Data" to queue all search results
- **Statistics**: Check Collection → Statistics menu for performance metrics

## Performance Optimization

### System Requirements
- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4+ CPU cores, 8GB+ RAM
- **High Performance**: 8+ CPU cores, 16GB+ RAM

### Configuration Tuning
```python
# For high-performance systems
config_manager.enable_high_performance_mode()

# For resource-constrained systems  
config_manager.enable_conservative_mode()

# Auto-optimize based on system specs
optimized_config = config_manager.get_optimized_config_for_system()
```

### Database Optimization
- **Connection Pool**: Adjust `max_connections` based on system resources
- **Concurrent Jobs**: Set `max_concurrent_jobs` to CPU cores - 1
- **Cache Settings**: Tune `cache_expiry_hours` based on data freshness needs

## Monitoring & Troubleshooting

### Performance Metrics
Access via Collection → Statistics menu:
- **Job Success Rate**: Percentage of successful data collections
- **Average Processing Time**: Time per job completion
- **Cache Hit Rate**: Efficiency of duplicate detection
- **Database Performance**: Connection pool utilization and query times

### Log Analysis
Key log entries to monitor:
```
INFO - Background data worker started
INFO - Queued 15 properties for background data collection  
INFO - Data collection completed for APN 12345678 in 45.3s
WARNING - Slow query detected - selects: 3.2s, 25/50 results
ERROR - Job for APN 87654321 failed after 3 retries
```

### Common Issues

**High CPU Usage**
- Reduce `max_concurrent_jobs` in configuration
- Enable `conservative_mode()`
- Check for inefficient web scraping selectors

**Database Connection Errors**
- Verify PostgreSQL max_connections setting
- Reduce `max_connections` in database_pool config
- Check database server resources

**Slow Data Collection**
- Verify internet connectivity to Maricopa County websites  
- Check web scraping timeout settings
- Consider increasing `job_timeout_seconds`

**Memory Usage**
- Monitor connection pool size
- Adjust cache expiry settings
- Check for memory leaks in long-running operations

## Advanced Features

### Custom Job Priorities
```python
# Critical priority for user-requested collections
background_manager.collect_data_for_apn(apn, JobPriority.CRITICAL)

# Bulk background enhancement  
background_manager.enhance_search_results(results, max_properties=50)
```

### Performance Callbacks
```python
# Monitor collection progress
background_manager.job_completed.connect(handle_job_completion)
background_manager.progress_updated.connect(update_ui_progress)
```

### Database Statistics
```python
# Get detailed performance stats
db_stats = db_manager.get_database_performance_stats()
collection_stats = background_manager.get_collection_status()
```

## Development Notes

### Adding New Data Sources
1. Extend `MaricopaDataCollector` in `automatic_data_collector.py`
2. Add new collection methods following async/await pattern
3. Update database schema for new data types
4. Modify UI to display new data fields

### Custom Priority Rules
1. Extend `JobPriority` enum in `background_data_collector.py`
2. Implement custom prioritization logic in `BackgroundDataWorker`
3. Update UI controls for priority selection

### Performance Monitoring
1. Add custom metrics to `DataCollectionStats` class
2. Implement monitoring callbacks in worker threads
3. Update UI components to display new metrics

## Security Considerations

### Data Protection
- All database connections use parameterized queries
- Web scraping respects robots.txt and rate limiting
- No sensitive data stored in logs or temporary files

### Concurrency Safety
- Thread-safe database operations with connection pooling
- Atomic upsert operations prevent data corruption
- Proper resource cleanup on application exit

### Error Handling
- Graceful degradation when external services are unavailable
- Automatic retry with exponential backoff
- Comprehensive error logging for troubleshooting

## Future Enhancements

### Planned Features
- **API Integration**: Direct integration with Maricopa County APIs
- **Machine Learning**: Predictive data collection based on search patterns
- **Distributed Processing**: Multi-node data collection for large operations
- **Real-time Updates**: WebSocket connections for live data updates

### Extensibility
- Plugin architecture for custom data sources
- Configurable collection strategies
- External notification systems (email, Slack, etc.)
- Integration with property valuation services

## Support & Contributing

### Getting Help
1. Check logs in `logs/` directory for error details
2. Review configuration with `enhanced_config_manager.py`
3. Test database connectivity with built-in connection tests
4. Monitor system resources during operation

### Contributing
1. Follow existing code patterns and documentation standards
2. Add comprehensive unit tests for new functionality  
3. Update this documentation for any architectural changes
4. Performance test changes under concurrent load

---

## Quick Start Checklist

- [ ] Install dependencies: `pip install PyQt5 psycopg2-binary playwright`
- [ ] Install browsers: `playwright install chromium`
- [ ] Configure database settings in `config.json`
- [ ] Test database connection: `python src/threadsafe_database_manager.py`
- [ ] Launch enhanced app: `python launch_enhanced_app.py`
- [ ] Verify background collection starts automatically
- [ ] Perform test search and confirm automatic data enhancement
- [ ] Check background status panel for active job processing
- [ ] Review collection statistics in menu

**Ready to transform your property search experience with seamless background data collection!**