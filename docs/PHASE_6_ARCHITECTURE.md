# Phase 6 Advanced Features - System Architecture Design

**Document Version**: 1.0
**Date**: September 18, 2025
**Phase**: SPARC Phase 3 - Architecture
**Status**: System Integration Design Complete

## Executive Summary

This document defines the comprehensive system architecture for integrating Phase 6 advanced features into the existing unified Maricopa Property Search application. The design maintains architectural integrity while introducing powerful new capabilities through strategic component enhancement and new service integration.

## Architecture Design Principles

### Unified Integration Strategy
- **Zero Breaking Changes**: All enhancements integrate seamlessly with existing unified components
- **Backward Compatibility**: Existing functionality remains unchanged
- **Performance Preservation**: New features enhance without degrading current performance
- **Cross-Platform Consistency**: Maintain WSL/Linux/Windows compatibility

### Scalability & Performance
- **Horizontal Scaling**: Components designed for multi-instance deployment
- **Resource Efficiency**: Intelligent resource allocation and monitoring
- **Caching Strategy**: Multi-layer caching for optimal performance
- **Load Distribution**: Intelligent workload distribution across system resources

### Quality & Reliability
- **Fault Tolerance**: Graceful degradation under failure conditions
- **Data Integrity**: Transactional consistency across all operations
- **Security Integration**: Comprehensive security at all architectural layers
- **Monitoring & Observability**: Complete system health visibility

## Current Architecture Foundation

### Existing Unified Components (Phase 2-5)
```
┌─────────────────────────────────────────────────────────────┐
│                   Current Unified Architecture             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ UnifiedGUI      │    │    UnifiedMaricopaAPIClient    │ │
│  │ Launcher        │◄──►│    • API → Web → Mock          │ │
│  │ • WSL/Linux/Win │    │    • 0.04s basic, 0.33s full  │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│           │                           │                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ UnifiedData     │    │  ThreadSafeDatabaseManager     │ │
│  │ Collector       │◄──►│  • PostgreSQL/SQLite/Mock      │ │
│  │ • Background    │    │  • Connection pooling          │ │
│  │ • Priority queue│    │  • Thread-safe operations      │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Quality Infrastructure (Phase 5)
- **GitHub Actions CI/CD**: 9-stage quality pipeline
- **Code Quality**: Black formatting, 80%+ test coverage
- **Security**: Bandit/Safety scanning, zero high-severity issues
- **Performance**: Automated benchmarking and regression testing

## Phase 6 Enhanced Architecture

### 1. Playwright Integration Layer

#### 1.1 Component Design
```python
# Enhanced UnifiedMaricopaAPIClient with Playwright integration
class UnifiedMaricopaAPIClient:
    """Enhanced API client with Playwright automation capabilities"""

    def __init__(self, config_manager: EnhancedConfigManager):
        # Existing initialization
        self.config = config_manager
        self.session = requests.Session()
        self.mock_mode = config_manager.get('database.use_mock', False)

        # New Playwright integration
        self.playwright_manager = PlaywrightAutomationManager(config_manager)
        self.cross_browser_tester = CrossBrowserTestManager(config_manager)
        self.performance_monitor = RealTimePerformanceMonitor(config_manager)

    # Enhanced web scraping method
    async def scrape_property_data_enhanced(
        self,
        apn: str,
        use_playwright: bool = True,
        browser_config: BrowserConfig = None
    ) -> PropertyData:
        """Enhanced web scraping with Playwright automation"""

        if use_playwright and self.playwright_manager.is_available():
            return await self.playwright_manager.scrape_property_data(
                apn=apn,
                browser_config=browser_config or self._get_default_browser_config()
            )
        else:
            # Fallback to existing BeautifulSoup method
            return self._scrape_with_beautifulsoup(apn)

    # New cross-browser testing capability
    async def validate_data_collection_cross_browser(
        self,
        test_properties: List[str],
        browser_matrix: List[str] = None
    ) -> CrossBrowserTestResult:
        """Validate data collection across multiple browsers"""

        return await self.cross_browser_tester.run_validation_tests(
            properties=test_properties,
            browsers=browser_matrix or ['chromium', 'firefox', 'webkit']
        )
```

#### 1.2 Playwright Service Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                Playwright Integration Layer                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Browser Pool    │  │ Performance     │  │ Visual      │ │
│  │ Manager         │  │ Monitor         │  │ Regression  │ │
│  │ • Chromium      │  │ • Core Web      │  │ Testing     │ │
│  │ • Firefox       │  │   Vitals        │  │ • Screenshot│ │
│  │ • WebKit        │  │ • Custom        │  │   Comparison│ │
│  │ • Resource      │  │   Metrics       │  │ • Baseline  │ │
│  │   Pooling       │  │ • Alerting      │  │   Management│ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                  │       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            PlaywrightAutomationManager                 │ │
│  │  • Browser context management                          │ │
│  │  • Session persistence                                 │ │
│  │  • Error recovery and retry logic                      │ │
│  │  • Performance optimization                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2. Advanced Search Services Layer

#### 2.1 Geospatial Search Integration
```python
# Enhanced UnifiedMaricopaAPIClient with geospatial capabilities
class UnifiedMaricopaAPIClient:
    def __init__(self, config_manager: EnhancedConfigManager):
        # Existing initialization...

        # New geospatial search integration
        self.geospatial_engine = GeospatialSearchEngine(config_manager)
        self.advanced_filters = AdvancedPropertyFilterEngine(config_manager)
        self.batch_processor = EnhancedBatchProcessor(config_manager)

    def search_properties_by_radius(
        self,
        center_address: str = None,
        center_coordinates: Tuple[float, float] = None,
        radius_miles: float = 1.0,
        property_filters: PropertyFilters = None
    ) -> GeospatialSearchResult:
        """Search properties within radius with advanced filtering"""

        # Resolve center coordinates
        if center_address:
            center_coords = self.geospatial_engine.geocode_address(center_address)
        else:
            center_coords = center_coordinates

        # Execute geospatial search
        return self.geospatial_engine.search_by_radius(
            center_point=center_coords,
            radius_miles=radius_miles,
            property_filters=property_filters
        )

    async def process_batch_search_file(
        self,
        file_path: str,
        column_mapping: Dict[str, str],
        processing_config: BatchProcessingConfig
    ) -> BatchSearchResult:
        """Process batch search from CSV/Excel file"""

        return await self.batch_processor.process_search_file(
            file_path=file_path,
            column_mapping=column_mapping,
            config=processing_config
        )
```

#### 2.2 Search Service Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                Advanced Search Services Layer               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Geospatial      │  │ Advanced        │  │ Search      │ │
│  │ Search Engine   │  │ Property        │  │ History     │ │
│  │ • Geocoding     │  │ Filters         │  │ Manager     │ │
│  │ • Spatial Index │  │ • Multi-criteria│  │ • Saved     │ │
│  │ • Radius Query  │  │ • Optimization  │  │   Searches  │ │
│  │ • Distance Calc │  │ • Performance   │  │ • Export    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                  │       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            Enhanced Batch Processor                     │ │
│  │  • CSV/Excel file processing                            │ │
│  │  • Column mapping and validation                        │ │
│  │  • Parallel processing with progress tracking           │ │
│  │  • Error handling and retry mechanisms                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 2.3 Database Schema Integration
```sql
-- Geospatial search support
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS earthdistance;
CREATE EXTENSION IF NOT EXISTS cube;

-- Enhanced property table with geospatial support
ALTER TABLE properties ADD COLUMN IF NOT EXISTS coordinates GEOGRAPHY(POINT, 4326);
ALTER TABLE properties ADD COLUMN IF NOT EXISTS geocoding_accuracy VARCHAR(20);
ALTER TABLE properties ADD COLUMN IF NOT EXISTS geocoding_source VARCHAR(50);

-- Spatial index for efficient radius queries
CREATE INDEX IF NOT EXISTS idx_properties_coordinates_gist
ON properties USING GIST (coordinates);

-- Additional indexes for advanced filtering
CREATE INDEX IF NOT EXISTS idx_properties_price_range
ON properties (assessed_value) WHERE assessed_value IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_properties_year_built
ON properties (year_built) WHERE year_built IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_properties_square_footage
ON properties (square_footage) WHERE square_footage IS NOT NULL;

-- Search history and saved searches
CREATE TABLE IF NOT EXISTS search_history (
    search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_type VARCHAR(50) NOT NULL,
    search_criteria JSONB NOT NULL,
    filters_applied JSONB,
    result_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_searches (
    saved_search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    search_criteria JSONB NOT NULL,
    filters JSONB,
    schedule_config JSONB,
    auto_export BOOLEAN DEFAULT FALSE,
    notification_settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for search performance
CREATE INDEX idx_search_history_type ON search_history(search_type);
CREATE INDEX idx_search_history_created ON search_history(created_at);
CREATE INDEX idx_saved_searches_name ON saved_searches(name);
```

### 3. Enhanced Batch Processing Architecture

#### 3.1 Multi-Threading Integration
```python
# Enhanced UnifiedDataCollector with multi-threading
class UnifiedDataCollector:
    """Enhanced data collector with multi-threading and advanced progress tracking"""

    def __init__(self, config_manager: EnhancedConfigManager):
        # Existing initialization...
        self.config = config_manager
        self.api_client = None
        self.database_manager = None

        # New multi-threading enhancements
        self.thread_pool_manager = ThreadPoolManager(config_manager)
        self.progress_tracker = AdvancedProgressTracker(config_manager)
        self.resource_monitor = ResourceMonitor(config_manager)
        self.export_manager = BulkExportManager(config_manager)

    async def collect_data_parallel(
        self,
        property_identifiers: List[str],
        collection_config: DataCollectionConfig,
        progress_callback: Callable = None
    ) -> ParallelCollectionResult:
        """Collect property data using multi-threading with progress tracking"""

        # Initialize progress tracking
        operation_handle = self.progress_tracker.start_operation(
            operation_type="parallel_data_collection",
            total_items=len(property_identifiers),
            supports_cancellation=True,
            supports_pause=True
        )

        try:
            # Execute parallel collection
            result = await self.thread_pool_manager.execute_parallel_collection(
                property_identifiers=property_identifiers,
                collection_config=collection_config,
                progress_tracker=self.progress_tracker,
                resource_monitor=self.resource_monitor
            )

            # Generate completion report
            completion_stats = self.progress_tracker.complete_operation(result)

            return ParallelCollectionResult(
                collected_data=result.successful_collections,
                errors=result.collection_errors,
                performance_metrics=completion_stats,
                resource_usage=self.resource_monitor.get_final_report()
            )

        except Exception as e:
            # Handle operation failure
            self.progress_tracker.fail_operation(str(e))
            raise

    async def export_bulk_data(
        self,
        collected_data: List[PropertyData],
        export_config: BulkExportConfig
    ) -> BulkExportResult:
        """Export collected data in various formats with custom formatting"""

        return await self.export_manager.export_properties(
            properties=collected_data,
            export_config=export_config
        )
```

#### 3.2 Enhanced Processing Architecture
```
┌─────────────────────────────────────────────────────────────┐
│            Enhanced Batch Processing Layer                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Thread Pool     │  │ Advanced        │  │ Resource    │ │
│  │ Manager         │  │ Progress        │  │ Monitor     │ │
│  │ • Dynamic       │  │ Tracker         │  │ • CPU Usage │ │
│  │   Scaling       │  │ • Pause/Resume  │  │ • Memory    │ │
│  │ • Load Balance  │  │ • Cancel        │  │ • Network   │ │
│  │ • Rate Limiting │  │ • Persistence   │  │ • Adaptive  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                  │       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │               Bulk Export Manager                       │ │
│  │  • Excel with formatting and charts                     │ │
│  │  • CSV with custom schemas                              │ │
│  │  • PDF reports with maps and visualizations             │ │
│  │  • JSON/XML for API integration                         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4. Real-Time Notifications System

#### 4.1 Notification Service Integration
```python
# New NotificationService integrated with existing components
class NotificationService:
    """Comprehensive notification system with multi-channel delivery"""

    def __init__(self, config_manager: EnhancedConfigManager):
        self.config = config_manager
        self.database_manager = None  # Injected by dependency injection

        # Notification components
        self.property_monitor = PropertyChangeMonitor(config_manager)
        self.market_alerter = MarketAlertSystem(config_manager)
        self.system_monitor = SystemHealthMonitor(config_manager)
        self.delivery_service = NotificationDeliveryService(config_manager)

    async def start_property_monitoring(
        self,
        property_identifiers: List[str],
        monitoring_config: PropertyMonitoringConfig
    ) -> List[MonitoringSession]:
        """Start monitoring properties for changes"""

        monitoring_sessions = []
        for property_id in property_identifiers:
            session = await self.property_monitor.start_monitoring(
                property_id=property_id,
                config=monitoring_config
            )
            monitoring_sessions.append(session)

        return monitoring_sessions

    async def setup_market_alerts(
        self,
        geographic_areas: List[GeographicArea],
        alert_criteria: MarketAlertCriteria,
        notification_preferences: NotificationPreferences
    ) -> List[MarketAlert]:
        """Setup market change alerts for geographic areas"""

        market_alerts = []
        for area in geographic_areas:
            alert = self.market_alerter.create_market_alert(
                area=area,
                criteria=alert_criteria,
                preferences=notification_preferences
            )
            market_alerts.append(alert)

        return market_alerts

# Integration with UnifiedDataCollector
class UnifiedDataCollector:
    def __init__(self, config_manager: EnhancedConfigManager):
        # Existing initialization...

        # Notification integration
        self.notification_service = NotificationService(config_manager)

    async def collect_data_with_notifications(
        self,
        property_identifiers: List[str],
        enable_change_monitoring: bool = False
    ) -> DataCollectionResult:
        """Collect data and optionally setup change monitoring"""

        # Execute data collection
        result = await self.collect_data_parallel(property_identifiers)

        # Setup change monitoring if requested
        if enable_change_monitoring:
            monitoring_sessions = await self.notification_service.start_property_monitoring(
                property_identifiers=property_identifiers,
                monitoring_config=self._get_default_monitoring_config()
            )
            result.monitoring_sessions = monitoring_sessions

        return result
```

#### 4.2 Notifications Architecture
```
┌─────────────────────────────────────────────────────────────┐
│               Real-Time Notifications System               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Property Change │  │ Market Alert    │  │ System      │ │
│  │ Monitor         │  │ System          │  │ Health      │ │
│  │ • Baseline      │  │ • Trend         │  │ Monitor     │ │
│  │   Tracking      │  │   Analysis      │  │ • API       │ │
│  │ • Change        │  │ • Threshold     │  │   Status    │ │
│  │   Detection     │  │   Monitoring    │  │ • Performance│ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                  │       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Notification Delivery Service                 │ │
│  │  • Email (SMTP with HTML templates)                     │ │
│  │  • SMS (Multiple providers: Twilio, AWS SNS)            │ │
│  │  • Push Notifications (Web push, mobile)                │ │
│  │  • In-App Notifications (Real-time GUI updates)         │ │
│  │  • Webhooks (Custom integrations)                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 4.3 Notification Database Schema
```sql
-- Notification subscriptions and preferences
CREATE TABLE IF NOT EXISTS notification_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    notification_type VARCHAR(50) NOT NULL,
    target_criteria JSONB NOT NULL,
    delivery_preferences JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification delivery history
CREATE TABLE IF NOT EXISTS notification_history (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES notification_subscriptions(subscription_id),
    notification_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    delivery_channels JSONB NOT NULL,
    delivery_status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    error_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Property monitoring sessions
CREATE TABLE IF NOT EXISTS property_monitoring (
    monitoring_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_apn VARCHAR(20) NOT NULL,
    monitoring_config JSONB NOT NULL,
    last_check_timestamp TIMESTAMP,
    last_known_state JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Property change detection log
CREATE TABLE IF NOT EXISTS property_changes (
    change_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_apn VARCHAR(20) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    previous_value JSONB,
    current_value JSONB,
    change_details JSONB,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE
);

-- Market alert configurations
CREATE TABLE IF NOT EXISTS market_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geographic_area JSONB NOT NULL,
    alert_criteria JSONB NOT NULL,
    notification_preferences JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_notification_subscriptions_user ON notification_subscriptions(user_id);
CREATE INDEX idx_notification_subscriptions_type ON notification_subscriptions(notification_type);
CREATE INDEX idx_notification_history_status ON notification_history(delivery_status);
CREATE INDEX idx_property_monitoring_apn ON property_monitoring(property_apn);
CREATE INDEX idx_property_changes_apn ON property_changes(property_apn);
CREATE INDEX idx_property_changes_detected ON property_changes(detected_at);
CREATE INDEX idx_market_alerts_active ON market_alerts(is_active);
```

## Unified System Integration

### 1. Enhanced Component Interaction Diagram
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      Phase 6 Enhanced Unified Architecture                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         UnifiedGUILauncher                              │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │ Enhanced    │ │ Geospatial  │ │ Batch       │ │ Notification    │  │   │
│  │  │ Search UI   │ │ Search UI   │ │ Processing  │ │ Management UI   │  │   │
│  │  │             │ │             │ │ UI          │ │                 │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Enhanced UnifiedMaricopaAPIClient                    │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │ Playwright  │ │ Geospatial  │ │ Advanced    │ │ Batch           │  │   │
│  │  │ Automation  │ │ Search      │ │ Filters     │ │ Processing      │  │   │
│  │  │ Manager     │ │ Engine      │ │ Engine      │ │ Manager         │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     Enhanced UnifiedDataCollector                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │ Multi-      │ │ Progress    │ │ Resource    │ │ Export          │  │   │
│  │  │ Threading   │ │ Tracker     │ │ Monitor     │ │ Manager         │  │   │
│  │  │ Manager     │ │             │ │             │ │                 │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Enhanced ThreadSafeDatabaseManager                   │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │ Geospatial  │ │ Search      │ │ Notification│ │ Performance     │  │   │
│  │  │ Extensions  │ │ History     │ │ Storage     │ │ Metrics         │  │   │
│  │  │             │ │ Manager     │ │             │ │ Storage         │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       NotificationService (New)                        │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │ Property    │ │ Market      │ │ System      │ │ Multi-Channel   │  │   │
│  │  │ Change      │ │ Alert       │ │ Health      │ │ Delivery        │  │   │
│  │  │ Monitor     │ │ System      │ │ Monitor     │ │ Service         │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Data Flow Integration
```
                              ┌─────────────────────┐
                              │   User Interface    │
                              │  • Search requests  │
                              │  • Progress display │
                              │  • Notifications    │
                              └─────────┬───────────┘
                                        │
                              ┌─────────▼───────────┐
                              │ UnifiedGUILauncher │
                              │ • Route requests    │
                              │ • Update displays   │
                              │ • Handle events     │
                              └─────────┬───────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
          ┌─────────▼───────────┐ ┌─────▼──────┐ ┌─────────▼────────┐
          │ UnifiedAPIClient    │ │ Enhanced   │ │ NotificationSvc  │
          │ • Playwright        │ │ DataColl   │ │ • Property Mon   │
          │ • Geospatial        │ │ • Multi-   │ │ • Market Alerts  │
          │ • Advanced Search   │ │   Threading│ │ • System Health  │
          │ • Batch Processing  │ │ • Progress │ │ • Delivery       │
          └─────────┬───────────┘ └─────┬──────┘ └─────────┬────────┘
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        │
                              ┌─────────▼───────────┐
                              │ ThreadSafeDBMgr    │
                              │ • Geospatial data  │
                              │ • Search history   │
                              │ • Notifications    │
                              │ • Performance      │
                              └────────────────────┘
```

### 3. Service Dependency Injection
```python
# Dependency injection container for Phase 6 services
class Phase6ServiceContainer:
    """Dependency injection container for enhanced services"""

    def __init__(self, config_manager: EnhancedConfigManager):
        self.config = config_manager
        self._services = {}

    def register_core_services(self):
        """Register all core enhanced services"""

        # Database manager (existing, enhanced)
        db_manager = ThreadSafeDatabaseManager(self.config)
        self._services['database'] = db_manager

        # Enhanced API client with new capabilities
        api_client = UnifiedMaricopaAPIClient(self.config)
        api_client.set_database_manager(db_manager)
        self._services['api_client'] = api_client

        # Enhanced data collector with multi-threading
        data_collector = UnifiedDataCollector(self.config)
        data_collector.set_api_client(api_client)
        data_collector.set_database_manager(db_manager)
        self._services['data_collector'] = data_collector

        # New notification service
        notification_service = NotificationService(self.config)
        notification_service.set_database_manager(db_manager)
        self._services['notification_service'] = notification_service

        # Enhanced GUI launcher with new features
        gui_launcher = UnifiedGUILauncher(self.config)
        gui_launcher.set_api_client(api_client)
        gui_launcher.set_data_collector(data_collector)
        gui_launcher.set_notification_service(notification_service)
        self._services['gui_launcher'] = gui_launcher

    def get_service(self, service_name: str):
        """Get service by name"""
        return self._services.get(service_name)

    def wire_dependencies(self):
        """Wire all service dependencies"""
        for service in self._services.values():
            if hasattr(service, 'wire_dependencies'):
                service.wire_dependencies(self)
```

## Configuration Management Integration

### 1. Enhanced Configuration Schema
```python
# Enhanced configuration schema for Phase 6 features
class Phase6ConfigurationSchema:
    """Configuration schema for Phase 6 advanced features"""

    def __init__(self):
        self.schema = {
            # Playwright browser automation
            'playwright': {
                'enabled': True,
                'browser': {
                    'default_browser': 'chromium',  # chromium, firefox, webkit
                    'headless': True,
                    'timeout': 30000,
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': 'MaricopaPropertySearch/3.0'
                },
                'performance_monitoring': {
                    'enabled': True,
                    'collection_interval': 5000,
                    'performance_budget': {
                        'page_load_time': 3000,
                        'api_response_time': 1000,
                        'memory_usage_mb': 512
                    }
                },
                'cross_browser_testing': {
                    'enabled': False,  # Disabled by default (resource intensive)
                    'browsers': ['chromium', 'firefox', 'webkit'],
                    'viewports': [
                        {'width': 1920, 'height': 1080},
                        {'width': 768, 'height': 1024},
                        {'width': 375, 'height': 667}
                    ]
                }
            },

            # Geospatial search configuration
            'geospatial': {
                'enabled': True,
                'geocoding': {
                    'provider': 'nominatim',  # nominatim, google, mapbox
                    'cache_duration_hours': 168,  # 1 week
                    'timeout_seconds': 10
                },
                'search': {
                    'default_radius_miles': 1.0,
                    'max_radius_miles': 50.0,
                    'spatial_index_enabled': True
                }
            },

            # Advanced property filters
            'property_filters': {
                'enabled': True,
                'optimization': {
                    'filter_ordering_enabled': True,
                    'early_termination_enabled': True,
                    'parallel_evaluation': False
                },
                'defaults': {
                    'allow_null_values': True,
                    'case_sensitive_text': False
                }
            },

            # Batch processing configuration
            'batch_processing': {
                'enabled': True,
                'threading': {
                    'max_workers': 'auto',  # 'auto' or integer
                    'dynamic_scaling': True,
                    'resource_monitoring': True
                },
                'file_processing': {
                    'max_file_size_mb': 100,
                    'supported_formats': ['csv', 'xlsx', 'xls', 'tsv'],
                    'chunk_size': 1000
                },
                'progress_tracking': {
                    'persistence_enabled': True,
                    'checkpoint_interval_seconds': 30,
                    'storage_path': 'data/progress'
                },
                'error_handling': {
                    'max_retries': 3,
                    'retry_delay_seconds': 1,
                    'max_error_rate': 0.2
                }
            },

            # Real-time notifications
            'notifications': {
                'enabled': True,
                'property_monitoring': {
                    'enabled': True,
                    'check_interval_minutes': 60,
                    'batch_size': 50
                },
                'market_alerts': {
                    'enabled': True,
                    'analysis_interval_hours': 6,
                    'trend_analysis_days': 30
                },
                'system_health': {
                    'enabled': True,
                    'check_interval_minutes': 5,
                    'alert_thresholds': {
                        'cpu_usage_percent': 80,
                        'memory_usage_percent': 85,
                        'disk_usage_percent': 90,
                        'api_error_rate': 0.1
                    }
                },
                'delivery': {
                    'email': {
                        'enabled': False,  # Requires SMTP configuration
                        'smtp_server': None,
                        'smtp_port': 587,
                        'use_tls': True,
                        'username': None,
                        'password': None
                    },
                    'sms': {
                        'enabled': False,  # Requires provider configuration
                        'provider': 'twilio',  # twilio, aws_sns
                        'api_key': None,
                        'api_secret': None
                    },
                    'push': {
                        'enabled': True,
                        'web_push_enabled': True
                    },
                    'in_app': {
                        'enabled': True,
                        'display_duration_seconds': 10
                    }
                }
            },

            # Export and reporting
            'export': {
                'enabled': True,
                'formats': {
                    'excel': {
                        'enabled': True,
                        'include_charts': True,
                        'include_formatting': True
                    },
                    'csv': {
                        'enabled': True,
                        'encoding': 'utf-8',
                        'delimiter': ','
                    },
                    'json': {
                        'enabled': True,
                        'pretty_print': True
                    },
                    'pdf': {
                        'enabled': False,  # Requires additional dependencies
                        'include_maps': False,
                        'template': 'standard'
                    }
                },
                'storage': {
                    'default_path': 'exports',
                    'max_file_size_mb': 500,
                    'cleanup_after_days': 30
                }
            }
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get the complete configuration schema"""
        return self.schema

    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        # Implementation would validate all required fields
        # and type constraints
        pass
```

## Performance Architecture

### 1. Caching Strategy
```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Layer Caching Strategy            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Level 1: In-Memory                 │   │
│  │  • Search results (LRU, 15min TTL)                 │   │
│  │  • Geocoding cache (LRU, 7 days TTL)               │   │
│  │  • Property data (LRU, 1 hour TTL)                 │   │
│  │  • Filter results (LRU, 30min TTL)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                │                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Level 2: Database                  │   │
│  │  • Property cache (24 hour freshness)              │   │
│  │  • Search history (permanent)                      │   │
│  │  • Notification state (permanent)                  │   │
│  │  • Performance metrics (30 days)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                │                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Level 3: File System                │   │
│  │  • Browser screenshots (7 days)                    │   │
│  │  • Export files (30 days)                          │   │
│  │  • Progress checkpoints (until completion)         │   │
│  │  • Performance reports (90 days)                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Resource Management
```python
class ResourceManager:
    """Unified resource management for all Phase 6 features"""

    def __init__(self, config: EnhancedConfigManager):
        self.config = config
        self.resource_limits = self._calculate_resource_limits()
        self.monitors = {
            'cpu': CPUMonitor(),
            'memory': MemoryMonitor(),
            'network': NetworkMonitor(),
            'browser': BrowserResourceMonitor()
        }

    def _calculate_resource_limits(self) -> ResourceLimits:
        """Calculate optimal resource limits based on system capabilities"""

        total_memory = psutil.virtual_memory().total
        cpu_count = psutil.cpu_count()

        return ResourceLimits(
            max_memory_usage_mb=int(total_memory * 0.6 / (1024 * 1024)),
            max_cpu_usage_percent=80,
            max_concurrent_browsers=min(cpu_count, 5),
            max_concurrent_threads=cpu_count * 2,
            max_batch_size=min(1000, total_memory // (100 * 1024 * 1024))
        )

    def allocate_resources(
        self,
        operation_type: str,
        estimated_requirements: ResourceRequirements
    ) -> ResourceAllocation:
        """Allocate resources for an operation"""

        current_usage = self.get_current_resource_usage()

        # Check if resources are available
        if not self._can_allocate(current_usage, estimated_requirements):
            raise InsufficientResourcesError(
                f"Cannot allocate resources for {operation_type}"
            )

        # Create resource allocation
        allocation = ResourceAllocation(
            operation_id=generate_uuid(),
            operation_type=operation_type,
            allocated_memory_mb=estimated_requirements.memory_mb,
            allocated_cpu_percent=estimated_requirements.cpu_percent,
            allocated_threads=estimated_requirements.threads,
            allocated_at=datetime.utcnow()
        )

        # Track allocation
        self._track_allocation(allocation)

        return allocation

    def release_resources(self, allocation: ResourceAllocation):
        """Release allocated resources"""
        self._untrack_allocation(allocation)

    def get_current_resource_usage(self) -> ResourceUsage:
        """Get current system resource usage"""
        return ResourceUsage(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_mb=psutil.virtual_memory().used // (1024 * 1024),
            memory_percent=psutil.virtual_memory().percent,
            active_threads=threading.active_count(),
            active_browsers=self.monitors['browser'].get_active_count()
        )
```

## Security Architecture Integration

### 1. Security Layer Enhancement
```python
class Phase6SecurityManager:
    """Enhanced security management for Phase 6 features"""

    def __init__(self, config: EnhancedConfigManager):
        self.config = config
        self.browser_security = BrowserSecurityManager()
        self.notification_security = NotificationSecurityManager()
        self.data_security = DataSecurityManager()

    def secure_browser_automation(
        self,
        browser_config: BrowserConfig
    ) -> SecureBrowserConfig:
        """Apply security policies to browser automation"""

        secure_config = SecureBrowserConfig(
            # Disable potentially dangerous features
            disable_web_security=False,
            disable_features=['background-sync', 'translate'],

            # Network security
            proxy_config=self._get_proxy_config(),
            user_agent=self._get_secure_user_agent(),

            # Content security
            block_mixed_content=True,
            disable_plugins=True,
            disable_extensions=True,

            # Privacy settings
            disable_background_networking=True,
            disable_sync=True,
            incognito_mode=True
        )

        return secure_config

    def validate_notification_delivery(
        self,
        notification: Notification,
        delivery_channels: List[str]
    ) -> ValidationResult:
        """Validate notification content and delivery channels"""

        # Validate notification content for sensitive information
        content_validation = self.notification_security.scan_content(
            notification.content
        )

        if content_validation.contains_sensitive_data:
            return ValidationResult(
                valid=False,
                reason="Notification contains sensitive information",
                blocked_fields=content_validation.sensitive_fields
            )

        # Validate delivery channels
        for channel in delivery_channels:
            channel_validation = self.notification_security.validate_channel(
                channel, notification.priority
            )

            if not channel_validation.valid:
                return ValidationResult(
                    valid=False,
                    reason=f"Channel {channel} not authorized: {channel_validation.reason}"
                )

        return ValidationResult(valid=True)

    def encrypt_sensitive_data(
        self,
        data: Dict[str, Any],
        classification: DataClassification
    ) -> EncryptedData:
        """Encrypt sensitive data based on classification"""

        if classification.level >= DataClassification.CONFIDENTIAL:
            return self.data_security.encrypt_data(
                data=data,
                encryption_key=self._get_encryption_key(classification),
                algorithm='AES-256-GCM'
            )
        else:
            return EncryptedData(data=data, encrypted=False)
```

## Quality Gates Integration

### 1. Phase 6 Quality Gate Framework
```python
class Phase6QualityGates:
    """Quality gate validation for Phase 6 features"""

    def __init__(self):
        self.gates = [
            PerformanceQualityGate(),
            SecurityQualityGate(),
            CompatibilityQualityGate(),
            FunctionalQualityGate(),
            ReliabilityQualityGate()
        ]

    async def validate_playwright_integration(
        self,
        test_scenarios: List[TestScenario]
    ) -> QualityGateResult:
        """Validate Playwright integration quality"""

        results = []

        for scenario in test_scenarios:
            # Performance validation
            perf_result = await self._validate_performance(scenario)
            results.append(perf_result)

            # Cross-browser compatibility
            compat_result = await self._validate_cross_browser(scenario)
            results.append(compat_result)

            # Security validation
            security_result = await self._validate_browser_security(scenario)
            results.append(security_result)

        return self._aggregate_results(results)

    async def validate_geospatial_search(
        self,
        test_properties: List[str]
    ) -> QualityGateResult:
        """Validate geospatial search quality"""

        # Accuracy validation
        accuracy_result = await self._validate_geocoding_accuracy(test_properties)

        # Performance validation
        perf_result = await self._validate_search_performance(test_properties)

        # Data integrity validation
        integrity_result = await self._validate_spatial_data_integrity(test_properties)

        return self._aggregate_results([accuracy_result, perf_result, integrity_result])

    async def validate_batch_processing(
        self,
        test_batch_size: int = 1000
    ) -> QualityGateResult:
        """Validate batch processing quality"""

        # Throughput validation
        throughput_result = await self._validate_processing_throughput(test_batch_size)

        # Resource management validation
        resource_result = await self._validate_resource_management(test_batch_size)

        # Error handling validation
        error_result = await self._validate_error_handling(test_batch_size)

        return self._aggregate_results([throughput_result, resource_result, error_result])

    async def validate_notification_system(
        self,
        test_scenarios: List[NotificationScenario]
    ) -> QualityGateResult:
        """Validate notification system quality"""

        # Delivery reliability validation
        delivery_result = await self._validate_delivery_reliability(test_scenarios)

        # Performance validation
        perf_result = await self._validate_notification_performance(test_scenarios)

        # Security validation
        security_result = await self._validate_notification_security(test_scenarios)

        return self._aggregate_results([delivery_result, perf_result, security_result])
```

## Deployment Architecture

### 1. Phase 6 Deployment Strategy
```
┌─────────────────────────────────────────────────────────────┐
│                Phase 6 Deployment Architecture             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Development Environment              │   │
│  │  • SQLite database                                  │   │
│  │  • Mock notification delivery                       │   │
│  │  • Single browser instance                          │   │
│  │  • Limited concurrency                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                │                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Testing Environment                  │   │
│  │  • PostgreSQL database                              │   │
│  │  • Full notification testing                        │   │
│  │  • Multi-browser testing                            │   │
│  │  • Performance benchmarking                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                │                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Production Environment               │   │
│  │  • PostgreSQL cluster                               │   │
│  │  • Redis caching layer                              │   │
│  │  • Load balanced browsers                           │   │
│  │  • Full monitoring and alerting                     │   │
│  │  • Backup and disaster recovery                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Migration Strategy

### 1. Backward Compatibility Preservation
```python
class Phase6MigrationManager:
    """Manage migration to Phase 6 features while preserving compatibility"""

    def __init__(self, config: EnhancedConfigManager):
        self.config = config
        self.migration_steps = [
            DatabaseSchemaMigration(),
            ConfigurationMigration(),
            ServiceIntegrationMigration(),
            DataMigration(),
            ValidationMigration()
        ]

    async def execute_migration(self) -> MigrationResult:
        """Execute Phase 6 migration"""

        migration_result = MigrationResult()

        for step in self.migration_steps:
            try:
                step_result = await step.execute()
                migration_result.add_step_result(step_result)

                if not step_result.success:
                    # Rollback on failure
                    await self._rollback_migration(step)
                    return migration_result

            except Exception as e:
                migration_result.add_error(step.__class__.__name__, str(e))
                await self._rollback_migration(step)
                return migration_result

        return migration_result

    async def validate_post_migration(self) -> ValidationResult:
        """Validate system after migration"""

        validation_tests = [
            ExistingFunctionalityTest(),
            NewFeatureIntegrationTest(),
            PerformanceRegressionTest(),
            CrossPlatformCompatibilityTest()
        ]

        results = []
        for test in validation_tests:
            result = await test.execute()
            results.append(result)

        return ValidationResult.aggregate(results)
```

## Quality Gate 3 ✅: Architecture Design Approved
- **System Integration**: Seamless integration with existing unified components
- **Performance Architecture**: Multi-layer caching, resource management, optimized data flows
- **Security Integration**: Comprehensive security at all architectural layers
- **Scalability Design**: Horizontal scaling capabilities with intelligent load distribution
- **Quality Framework**: Comprehensive quality gates for all new features
- **Migration Strategy**: Zero breaking changes with backward compatibility preservation

**Next Phase**: SPARC Phase 4 - Refinement Planning
**Coordination**: Refinement agent ready for iterative improvement and optimization strategies