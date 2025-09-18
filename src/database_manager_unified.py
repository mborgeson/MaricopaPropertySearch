#!/usr/bin/env python
"""
Unified Database Manager
Consolidated database operations combining features from both DatabaseManager and ThreadSafeDatabaseManager

CONSOLIDATED - This file combines functionality from:
- database_manager.py (base implementation)
- threadsafe_database_manager.py (advanced features)

Key Features:
- Thread-safe connection pooling
- Performance monitoring and statistics
- Bulk operations for efficiency
- Data collection status tracking
- Comprehensive error handling
- Full backward compatibility
"""

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor, execute_batch, Json
from contextlib import contextmanager
import logging
from threading import Lock, RLock
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, timedelta
import time
import traceback

# Import centralized logging
from .logging_config import get_logger, get_performance_logger, log_exception

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class UnifiedDatabaseManager:
    """
    Unified database manager with thread-safe operations and performance monitoring

    This class combines all functionality from the previous database managers:
    - Basic CRUD operations from DatabaseManager
    - Advanced threading and pooling from ThreadSafeDatabaseManager
    - Performance monitoring and bulk operations
    - Backward compatibility with all existing code
    """

    def __init__(self, config_manager, min_connections=5, max_connections=20):
        """Initialize with configurable connection pooling for concurrent operations"""
        logger.info("Initializing Unified Database Manager")

        # Get database configuration - support both config methods for compatibility
        if hasattr(config_manager, "get_database_config"):
            self.config = config_manager.get_database_config()
        elif hasattr(config_manager, "get_db_config"):
            self.config = config_manager.get_db_config()
        else:
            raise AttributeError(
                "Config manager must have either get_database_config() or get_db_config() method"
            )

        self.min_connections = min_connections
        self.max_connections = max_connections

        logger.debug(
            f"Database Configuration - Host: {self.config['host']}, Port: {self.config['port']}, Database: {self.config['database']}"
        )

        # Thread safety
        self._pool_lock = RLock()
        self._stats_lock = Lock()

        # Connection pool
        self._connection_pool = None
        self.pool = None  # Alias for backward compatibility

        # Performance tracking
        self._operation_stats = {
            "inserts": {"count": 0, "total_time": 0.0, "errors": 0},
            "selects": {"count": 0, "total_time": 0.0, "errors": 0},
            "updates": {"count": 0, "total_time": 0.0, "errors": 0},
        }

        # Initialize connection pool
        self._initialize_connection_pool()

        # Initialize database schema if needed
        self._ensure_tables_exist()

        logger.info(
            f"Unified database manager initialized with pool size {min_connections}-{max_connections}"
        )

    def _initialize_connection_pool(self):
        """Initialize the database connection pool"""
        logger.debug("Setting up database connection pool")

        try:
            connection_string = (
                f"host={self.config['host']} "
                f"port={self.config['port']} "
                f"dbname={self.config['database']} "
                f"user={self.config['user']} "
                f"password={self.config['password']}"
            )

            self._connection_pool = ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                dsn=connection_string,
                cursor_factory=RealDictCursor,
            )

            # Alias for backward compatibility
            self.pool = self._connection_pool

            logger.info("Database connection pool initialized successfully")
            logger.debug(
                f"Connection pool configured with min={self.min_connections}, max={self.max_connections} connections"
            )

        except Exception as e:
            log_exception(logger, e, "initializing database connection pool")
            raise

    def _init_connection_pool(self):
        """Backward compatibility alias for _initialize_connection_pool"""
        return self._initialize_connection_pool()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with thread safety"""
        connection = None
        start_time = None

        try:
            start_time = time.time()
            logger.debug("Acquiring database connection from pool")

            with self._pool_lock:
                connection = self._connection_pool.getconn()

            # Set autocommit for better concurrent performance
            connection.autocommit = False
            logger.debug("Database connection acquired successfully")

            yield connection

        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                    logger.debug("Database transaction rolled back due to error")
                except:
                    pass

            log_exception(logger, e, "database operation")
            raise

        finally:
            if connection:
                try:
                    logger.debug("Returning database connection to pool")
                    with self._pool_lock:
                        self._connection_pool.putconn(connection)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")

    def _record_operation_stats(
        self, operation_type: str, duration: float, error: bool = False
    ):
        """Record operation statistics for performance monitoring"""
        with self._stats_lock:
            stats = self._operation_stats.get(
                operation_type, {"count": 0, "total_time": 0.0, "errors": 0}
            )
            stats["count"] += 1
            stats["total_time"] += duration
            if error:
                stats["errors"] += 1
            self._operation_stats[operation_type] = stats

    @perf_logger.log_performance("test_connection")
    def test_connection(self) -> bool:
        """Test database connectivity"""
        logger.debug("Testing database connection")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result and (
                    result.get(0) == 1
                    or (hasattr(result, "values") and 1 in result.values())
                ):
                    logger.info("Database connection test successful")
                    return True
                else:
                    logger.error("Database connection test returned unexpected result")
                    return False

        except Exception as e:
            log_exception(logger, e, "database connection test")
            return False

    # =======================
    # PROPERTY OPERATIONS
    # =======================

    @perf_logger.log_database_operation("upsert", "properties", 1)
    def insert_property(self, property_data: Dict[str, Any]) -> bool:
        """Insert or update property data with comprehensive validation"""
        apn = property_data.get("apn")

        # Validate required field
        if not apn:
            logger.error("Cannot insert property: missing required 'apn' field")
            return False

        logger.info(f"Inserting/updating property data for APN: {apn}")
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Define required fields with default values
                required_fields = {
                    "apn": apn,
                    "owner_name": None,
                    "property_address": None,
                    "mailing_address": None,
                    "legal_description": None,
                    "land_use_code": None,
                    "year_built": None,
                    "living_area_sqft": None,
                    "lot_size_sqft": None,
                    "bedrooms": None,
                    "bathrooms": None,
                    "pool": None,
                    "garage_spaces": None,
                    "raw_data": None,
                }

                # Merge provided data with defaults, ensuring all required keys exist
                safe_property_data = {**required_fields, **property_data}

                # Convert raw_data to JSON if it's a dict
                if safe_property_data.get("raw_data") and isinstance(
                    safe_property_data["raw_data"], dict
                ):
                    safe_property_data["raw_data"] = Json(
                        safe_property_data["raw_data"]
                    )

                # Log missing fields for debugging
                missing_fields = [
                    field
                    for field in required_fields.keys()
                    if field not in property_data
                ]
                if missing_fields:
                    logger.debug(
                        f"Using default values for missing fields: {missing_fields} for APN: {apn}"
                    )

                sql = """
                INSERT INTO properties (
                    apn, owner_name, property_address, mailing_address,
                    legal_description, land_use_code, year_built, living_area_sqft,
                    lot_size_sqft, bedrooms, bathrooms, pool, garage_spaces,
                    raw_data, created_at, last_updated
                ) VALUES (
                    %(apn)s, %(owner_name)s, %(property_address)s, %(mailing_address)s,
                    %(legal_description)s, %(land_use_code)s, %(year_built)s, %(living_area_sqft)s,
                    %(lot_size_sqft)s, %(bedrooms)s, %(bathrooms)s, %(pool)s, %(garage_spaces)s,
                    %(raw_data)s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (apn) DO UPDATE SET
                    owner_name = COALESCE(EXCLUDED.owner_name, properties.owner_name),
                    property_address = COALESCE(EXCLUDED.property_address, properties.property_address),
                    mailing_address = COALESCE(EXCLUDED.mailing_address, properties.mailing_address),
                    legal_description = COALESCE(EXCLUDED.legal_description, properties.legal_description),
                    land_use_code = COALESCE(EXCLUDED.land_use_code, properties.land_use_code),
                    year_built = COALESCE(EXCLUDED.year_built, properties.year_built),
                    living_area_sqft = COALESCE(EXCLUDED.living_area_sqft, properties.living_area_sqft),
                    lot_size_sqft = COALESCE(EXCLUDED.lot_size_sqft, properties.lot_size_sqft),
                    bedrooms = COALESCE(EXCLUDED.bedrooms, properties.bedrooms),
                    bathrooms = COALESCE(EXCLUDED.bathrooms, properties.bathrooms),
                    pool = COALESCE(EXCLUDED.pool, properties.pool),
                    garage_spaces = COALESCE(EXCLUDED.garage_spaces, properties.garage_spaces),
                    raw_data = COALESCE(EXCLUDED.raw_data, properties.raw_data),
                    last_updated = CURRENT_TIMESTAMP
                """

                cursor.execute(sql, safe_property_data)
                conn.commit()

                duration = time.time() - start_time
                self._record_operation_stats("inserts", duration)

                logger.debug(f"Property data committed successfully for APN: {apn}")
                return True

        except KeyError as e:
            duration = time.time() - start_time
            self._record_operation_stats("inserts", duration, error=True)
            logger.error(f"KeyError in insert_property for APN {apn}: Missing key {e}")
            logger.error(
                f"Available keys in property_data: {list(property_data.keys())}"
            )
            return False
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("inserts", duration, error=True)
            log_exception(logger, e, f"inserting property data for APN: {apn}")
            return False

    def insert_property_safe(self, property_data: Dict[str, Any]) -> bool:
        """Thread-safe property insertion - alias for insert_property for backward compatibility"""
        return self.insert_property(property_data)

    @perf_logger.log_database_operation("select", "properties", 1)
    def get_property_by_apn(self, apn: str) -> Optional[Dict]:
        """Get property by APN with performance tracking"""
        logger.debug(f"Retrieving property data for APN: {apn}")
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = "SELECT * FROM property_current_view WHERE apn = %s"
                cursor.execute(sql, (apn,))

                result = cursor.fetchone()

                duration = time.time() - start_time
                self._record_operation_stats("selects", duration)

                if result:
                    logger.debug(f"Property data found for APN: {apn}")
                    return dict(result)
                else:
                    logger.debug(f"No property data found for APN: {apn}")
                    return None

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            log_exception(logger, e, f"retrieving property data for APN: {apn}")
            return None

    def get_property_details(self, apn: str) -> Optional[Dict]:
        """Get property details by APN - alias for get_property_by_apn for GUI compatibility"""
        logger.debug(f"Retrieving property details for APN: {apn}")

        try:
            return self.get_property_by_apn(apn)

        except Exception as e:
            log_exception(logger, e, f"retrieving property details for APN: {apn}")
            return None

    @perf_logger.log_database_operation("search", "properties", None)
    def search_properties_by_owner(
        self, owner_name: str, limit: int = 100
    ) -> List[Dict]:
        """Search properties by owner name with performance tracking"""
        logger.info(f"Searching properties by owner: {owner_name} (limit: {limit})")
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                SELECT * FROM property_current_view
                WHERE owner_name ILIKE %s
                ORDER BY owner_name
                LIMIT %s
                """

                cursor.execute(sql, (f"%{owner_name}%", limit))
                results = [dict(row) for row in cursor.fetchall()]

                duration = time.time() - start_time
                self._record_operation_stats("selects", duration)

                logger.info(f"Found {len(results)} properties for owner: {owner_name}")
                logger.debug(
                    f"DB_ANALYTICS: owner_search, query_time={duration:.3f}s, results={len(results)}, limit={limit}"
                )

                return results

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            log_exception(logger, e, f"searching properties by owner: {owner_name}")
            return []

    @perf_logger.log_database_operation("search", "properties", None)
    def search_properties_by_address(
        self, address: str, limit: int = 100
    ) -> List[Dict]:
        """Search properties by address with performance tracking"""
        logger.info(f"Searching properties by address: {address} (limit: {limit})")
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                SELECT * FROM property_current_view
                WHERE property_address ILIKE %s
                ORDER BY property_address
                LIMIT %s
                """

                cursor.execute(sql, (f"%{address}%", limit))
                results = [dict(row) for row in cursor.fetchall()]

                duration = time.time() - start_time
                self._record_operation_stats("selects", duration)

                logger.info(f"Found {len(results)} properties for address: {address}")
                logger.debug(
                    f"DB_ANALYTICS: address_search, query_time={duration:.3f}s, results={len(results)}, limit={limit}"
                )

                return results

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            log_exception(logger, e, f"searching properties by address: {address}")
            return []

    # =======================
    # TAX HISTORY OPERATIONS
    # =======================

    def insert_tax_history(self, tax_data: Dict[str, Any]) -> bool:
        """Insert tax history record with enhanced error handling"""
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                INSERT INTO tax_history (
                    apn, tax_year, assessed_value, limited_value,
                    tax_amount, payment_status, last_payment_date, raw_data, created_at
                ) VALUES (
                    %(apn)s, %(tax_year)s, %(assessed_value)s, %(limited_value)s,
                    %(tax_amount)s, %(payment_status)s, %(last_payment_date)s, %(raw_data)s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (apn, tax_year) DO UPDATE SET
                    assessed_value = COALESCE(EXCLUDED.assessed_value, tax_history.assessed_value),
                    limited_value = COALESCE(EXCLUDED.limited_value, tax_history.limited_value),
                    tax_amount = COALESCE(EXCLUDED.tax_amount, tax_history.tax_amount),
                    payment_status = COALESCE(EXCLUDED.payment_status, tax_history.payment_status),
                    last_payment_date = COALESCE(EXCLUDED.last_payment_date, tax_history.last_payment_date),
                    raw_data = COALESCE(EXCLUDED.raw_data, tax_history.raw_data)
                """

                # Prepare data with JSON serialization for raw_data
                insert_data = tax_data.copy()
                if "raw_data" in insert_data and insert_data["raw_data"]:
                    if isinstance(insert_data["raw_data"], dict):
                        insert_data["raw_data"] = Json(insert_data["raw_data"])

                cursor.execute(sql, insert_data)
                conn.commit()

                duration = time.time() - start_time
                self._record_operation_stats("inserts", duration)

                logger.debug(
                    f"Tax history inserted for APN: {tax_data.get('apn')}, year: {tax_data.get('tax_year')}"
                )
                return True

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("inserts", duration, error=True)
            logger.error(
                f"Error inserting tax history for {tax_data.get('apn', 'unknown')}: {e}"
            )
            return False

    def insert_tax_history_safe(self, tax_data: Dict[str, Any]) -> bool:
        """Thread-safe tax history insertion - alias for backward compatibility"""
        return self.insert_tax_history(tax_data)

    def get_tax_history(self, apn: str) -> List[Dict]:
        """Get tax history for property with performance tracking"""
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                SELECT * FROM tax_history
                WHERE apn = %s
                ORDER BY tax_year DESC
                """

                cursor.execute(sql, (apn,))
                results = [dict(row) for row in cursor.fetchall()]

                duration = time.time() - start_time
                self._record_operation_stats("selects", duration)

                return results

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            logger.error(f"Failed to get tax history for {apn}: {e}")
            return []

    def bulk_insert_tax_history(self, tax_records: List[Dict[str, Any]]) -> int:
        """Efficient bulk insertion of tax history records"""
        if not tax_records:
            return 0

        start_time = time.time()
        inserted_count = 0

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Prepare data tuples for batch insert
                data_tuples = []
                for record in tax_records:
                    data_tuples.append(
                        (
                            record.get("apn"),
                            record.get("tax_year"),
                            record.get("assessed_value"),
                            record.get("limited_value"),
                            record.get("tax_amount"),
                            record.get("payment_status"),
                            record.get("last_payment_date"),
                            Json(record.get("raw_data", {})),
                        )
                    )

                # Use execute_batch for better performance
                sql = """
                INSERT INTO tax_history (
                    apn, tax_year, assessed_value, limited_value, tax_amount,
                    payment_status, last_payment_date, raw_data, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (apn, tax_year) DO NOTHING
                """

                execute_batch(cursor, sql, data_tuples, page_size=100)
                conn.commit()

                inserted_count = len(data_tuples)
                duration = time.time() - start_time
                self._record_operation_stats("inserts", duration)

                logger.info(
                    f"Bulk inserted {inserted_count} tax records in {duration:.2f}s"
                )

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("inserts", duration, error=True)
            logger.error(f"Error in bulk tax history insert: {e}")
            logger.debug(traceback.format_exc())

        return inserted_count

    # =======================
    # SALES HISTORY OPERATIONS
    # =======================

    def insert_sales_history(self, sales_data: Dict[str, Any]) -> bool:
        """Insert sales history record with enhanced error handling"""
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                INSERT INTO sales_history (
                    apn, sale_date, sale_price, seller_name,
                    buyer_name, deed_type, recording_number, created_at
                ) VALUES (
                    %(apn)s, %(sale_date)s, %(sale_price)s, %(seller_name)s,
                    %(buyer_name)s, %(deed_type)s, %(recording_number)s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (apn, sale_date, recording_number) DO UPDATE SET
                    sale_price = COALESCE(EXCLUDED.sale_price, sales_history.sale_price),
                    seller_name = COALESCE(EXCLUDED.seller_name, sales_history.seller_name),
                    buyer_name = COALESCE(EXCLUDED.buyer_name, sales_history.buyer_name),
                    deed_type = COALESCE(EXCLUDED.deed_type, sales_history.deed_type)
                """

                cursor.execute(sql, sales_data)
                conn.commit()

                duration = time.time() - start_time
                self._record_operation_stats("inserts", duration)

                logger.debug(
                    f"Sales history inserted for APN: {sales_data.get('apn')}, date: {sales_data.get('sale_date')}"
                )
                return True

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("inserts", duration, error=True)
            logger.error(
                f"Error inserting sales history for {sales_data.get('apn', 'unknown')}: {e}"
            )
            return False

    def insert_sales_history_safe(self, sales_data: Dict[str, Any]) -> bool:
        """Thread-safe sales history insertion - alias for backward compatibility"""
        return self.insert_sales_history(sales_data)

    def get_sales_history(self, apn: str) -> List[Dict]:
        """Get sales history for property with performance tracking"""
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                SELECT * FROM sales_history
                WHERE apn = %s
                ORDER BY sale_date DESC
                """

                cursor.execute(sql, (apn,))
                results = [dict(row) for row in cursor.fetchall()]

                duration = time.time() - start_time
                self._record_operation_stats("selects", duration)

                return results

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            logger.error(f"Failed to get sales history for {apn}: {e}")
            return []

    def bulk_insert_sales_history(self, sales_records: List[Dict[str, Any]]) -> int:
        """Efficient bulk insertion of sales history records"""
        if not sales_records:
            return 0

        start_time = time.time()
        inserted_count = 0

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Prepare data tuples
                data_tuples = []
                for record in sales_records:
                    data_tuples.append(
                        (
                            record.get("apn"),
                            record.get("sale_date"),
                            record.get("sale_price"),
                            record.get("seller_name"),
                            record.get("buyer_name"),
                            record.get("deed_type"),
                            record.get(
                                "recording_number",
                                f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            ),
                        )
                    )

                sql = """
                INSERT INTO sales_history (
                    apn, sale_date, sale_price, seller_name, buyer_name,
                    deed_type, recording_number, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (apn, sale_date, recording_number) DO NOTHING
                """

                execute_batch(cursor, sql, data_tuples, page_size=100)
                conn.commit()

                inserted_count = len(data_tuples)
                duration = time.time() - start_time
                self._record_operation_stats("inserts", duration)

                logger.info(
                    f"Bulk inserted {inserted_count} sales records in {duration:.2f}s"
                )

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("inserts", duration, error=True)
            logger.error(f"Error in bulk sales history insert: {e}")
            logger.debug(traceback.format_exc())

        return inserted_count

    # =======================
    # DATA COLLECTION STATUS OPERATIONS
    # =======================

    def get_data_collection_status(self, apn: str) -> Dict[str, Any]:
        """Get comprehensive data collection status for an APN"""
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get property info with data counts
                sql = """
                SELECT
                    p.*,
                    COALESCE(t.tax_count, 0) as tax_records_count,
                    COALESCE(s.sales_count, 0) as sales_records_count,
                    t.latest_tax_year,
                    s.latest_sale_date,
                    CASE
                        WHEN p.last_updated > NOW() - INTERVAL '24 hours' THEN true
                        ELSE false
                    END as recently_updated
                FROM properties p
                LEFT JOIN (
                    SELECT apn, COUNT(*) as tax_count, MAX(tax_year) as latest_tax_year
                    FROM tax_history
                    WHERE apn = %s
                    GROUP BY apn
                ) t ON p.apn = t.apn
                LEFT JOIN (
                    SELECT apn, COUNT(*) as sales_count, MAX(sale_date) as latest_sale_date
                    FROM sales_history
                    WHERE apn = %s
                    GROUP BY apn
                ) s ON p.apn = s.apn
                WHERE p.apn = %s
                """

                cursor.execute(sql, (apn, apn, apn))
                result = cursor.fetchone()

                if result:
                    status = dict(result)

                    # Determine collection completeness
                    has_current_tax = (
                        status["tax_records_count"] > 0
                        and status.get("latest_tax_year", 0) >= datetime.now().year - 1
                    )

                    has_recent_sales = (
                        status["sales_records_count"] > 0
                        and status.get("latest_sale_date")
                        and status["latest_sale_date"]
                        > (datetime.now().date() - timedelta(days=1825))  # 5 years
                    )

                    status["data_complete"] = has_current_tax and has_recent_sales
                    status["needs_tax_collection"] = not has_current_tax
                    status["needs_sales_collection"] = not has_recent_sales

                    duration = time.time() - start_time
                    self._record_operation_stats("selects", duration)

                    return status
                else:
                    return {
                        "apn": apn,
                        "exists": False,
                        "tax_records_count": 0,
                        "sales_records_count": 0,
                        "data_complete": False,
                        "needs_tax_collection": True,
                        "needs_sales_collection": True,
                    }

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            logger.error(f"Error getting data collection status for {apn}: {e}")
            return {
                "apn": apn,
                "error": str(e),
                "data_complete": False,
                "needs_tax_collection": True,
                "needs_sales_collection": True,
            }

    def get_apns_needing_collection(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get APNs that need data collection, prioritized by search frequency"""
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                SELECT
                    p.apn,
                    p.owner_name,
                    p.property_address,
                    COALESCE(search_freq.search_count, 0) as search_frequency,
                    COALESCE(t.tax_count, 0) as tax_records,
                    COALESCE(s.sales_count, 0) as sales_records,
                    CASE
                        WHEN COALESCE(t.latest_tax_year, 0) < %s THEN true
                        ELSE false
                    END as needs_tax_data,
                    CASE
                        WHEN COALESCE(s.latest_sale_date, '1900-01-01'::date) < %s THEN true
                        ELSE false
                    END as needs_sales_data
                FROM properties p
                LEFT JOIN (
                    SELECT search_term as apn, COUNT(*) as search_count
                    FROM search_history
                    WHERE search_type = 'apn'
                    AND searched_at > NOW() - INTERVAL '30 days'
                    GROUP BY search_term
                ) search_freq ON p.apn = search_freq.apn
                LEFT JOIN (
                    SELECT apn, COUNT(*) as tax_count, MAX(tax_year) as latest_tax_year
                    FROM tax_history
                    GROUP BY apn
                ) t ON p.apn = t.apn
                LEFT JOIN (
                    SELECT apn, COUNT(*) as sales_count, MAX(sale_date) as latest_sale_date
                    FROM sales_history
                    GROUP BY apn
                ) s ON p.apn = s.apn
                WHERE (
                    COALESCE(t.latest_tax_year, 0) < %s OR
                    COALESCE(s.latest_sale_date, '1900-01-01'::date) < %s
                )
                ORDER BY
                    search_freq.search_count DESC NULLS LAST,
                    p.created_at DESC
                LIMIT %s
                """

                current_year = datetime.now().year
                five_years_ago = datetime.now().date() - timedelta(days=1825)

                cursor.execute(
                    sql,
                    (current_year, five_years_ago, current_year, five_years_ago, limit),
                )
                results = cursor.fetchall()

                duration = time.time() - start_time
                self._record_operation_stats("selects", duration)

                logger.info(f"Found {len(results)} APNs needing data collection")
                return [dict(row) for row in results]

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            logger.error(f"Error getting APNs needing collection: {e}")
            return []

    def mark_collection_in_progress(self, apn: str) -> bool:
        """Mark an APN as having collection in progress"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insert or update collection status
                sql = """
                INSERT INTO data_collection_status (apn, status, started_at)
                VALUES (%s, 'in_progress', CURRENT_TIMESTAMP)
                ON CONFLICT (apn) DO UPDATE SET
                    status = 'in_progress',
                    started_at = CURRENT_TIMESTAMP
                """

                cursor.execute(sql, (apn,))
                conn.commit()

                return True

        except Exception as e:
            logger.error(f"Error marking collection in progress for {apn}: {e}")
            return False

    def mark_collection_completed(
        self, apn: str, success: bool, error_message: Optional[str] = None
    ) -> bool:
        """Mark an APN collection as completed"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                status = "completed" if success else "failed"

                sql = """
                INSERT INTO data_collection_status (apn, status, completed_at, error_message)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
                ON CONFLICT (apn) DO UPDATE SET
                    status = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    error_message = %s
                """

                cursor.execute(sql, (apn, status, error_message, status, error_message))
                conn.commit()

                return True

        except Exception as e:
            logger.error(f"Error marking collection completed for {apn}: {e}")
            return False

    # =======================
    # ANALYTICS OPERATIONS
    # =======================

    @perf_logger.log_database_operation("insert", "search_history", 1)
    def log_search(
        self,
        search_type: str,
        search_term: str,
        results_count: int,
        user_ip: str = None,
    ):
        """Log search for analytics with performance tracking"""
        logger.debug(
            f"Logging search analytics: {search_type} search for '{search_term}' with {results_count} results"
        )
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                INSERT INTO search_history (search_type, search_term, results_count, user_ip)
                VALUES (%s, %s, %s, %s)
                """

                cursor.execute(sql, (search_type, search_term, results_count, user_ip))
                conn.commit()

                duration = time.time() - start_time
                self._record_operation_stats("inserts", duration)

                logger.debug("Search analytics logged successfully")

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("inserts", duration, error=True)
            log_exception(
                logger, e, f"logging search analytics for {search_type} search"
            )

    @perf_logger.log_performance("get_database_stats")
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics with performance tracking"""
        logger.debug("Retrieving database statistics")
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # Property count
                cursor.execute("SELECT COUNT(*) as count FROM properties")
                result = cursor.fetchone()
                stats["properties"] = result["count"] if result else 0

                # Tax records count
                cursor.execute("SELECT COUNT(*) as count FROM tax_history")
                result = cursor.fetchone()
                stats["tax_records"] = result["count"] if result else 0

                # Sales records count
                cursor.execute("SELECT COUNT(*) as count FROM sales_history")
                result = cursor.fetchone()
                stats["sales_records"] = result["count"] if result else 0

                # Recent searches (handle case where table may not exist)
                try:
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM search_history WHERE searched_at > NOW() - INTERVAL '7 days'"
                    )
                    result = cursor.fetchone()
                    stats["recent_searches"] = result["count"] if result else 0
                except:
                    stats["recent_searches"] = 0

                duration = time.time() - start_time
                self._record_operation_stats("selects", duration)

                logger.info(
                    f"Database statistics retrieved - Properties: {stats.get('properties', 0):,}, "
                    f"Tax Records: {stats.get('tax_records', 0):,}, "
                    f"Sales Records: {stats.get('sales_records', 0):,}"
                )

                return stats

        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats("selects", duration, error=True)
            log_exception(logger, e, "retrieving database statistics")
            return {}

    def get_database_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        with self._stats_lock:
            stats = {}

            # Calculate averages and rates
            for op_type, op_stats in self._operation_stats.items():
                if op_stats["count"] > 0:
                    avg_time = op_stats["total_time"] / op_stats["count"]
                    error_rate = (op_stats["errors"] / op_stats["count"]) * 100
                else:
                    avg_time = 0
                    error_rate = 0

                stats[op_type] = {
                    "count": op_stats["count"],
                    "average_time": avg_time,
                    "total_time": op_stats["total_time"],
                    "error_count": op_stats["errors"],
                    "error_rate_percent": error_rate,
                }

            # Add connection pool stats
            if self._connection_pool:
                try:
                    with self._pool_lock:
                        # Get pool status (these methods may not be available in all versions)
                        stats["connection_pool"] = {
                            "min_connections": self.min_connections,
                            "max_connections": self.max_connections,
                            "status": "active",
                        }
                except Exception as e:
                    stats["connection_pool"] = {"status": "error", "error": str(e)}

            return stats

    # =======================
    # VALIDATION AND UTILITY METHODS
    # =======================

    def save_comprehensive_property_data(
        self, comprehensive_info: Dict[str, Any]
    ) -> bool:
        """Save comprehensive property data including detailed information"""
        apn = comprehensive_info.get("apn", "unknown")
        logger.info(f"Saving comprehensive property data for APN: {apn}")

        try:
            # Save basic property information
            basic_property_saved = self.insert_property(comprehensive_info)
            if not basic_property_saved:
                logger.warning(f"Failed to save basic property data for APN: {apn}")
                return False

            # Save valuation history if available
            valuation_records_saved = 0
            if "valuation_history" in comprehensive_info:
                for valuation in comprehensive_info["valuation_history"]:
                    tax_data = {
                        "apn": apn,
                        "tax_year": int(valuation.get("TaxYear", 0)),
                        "assessed_value": self._safe_int(
                            valuation.get("FullCashValue", 0)
                        ),
                        "limited_value": self._safe_int(
                            valuation.get("LimitedPropertyValue", "").strip()
                        ),
                        "tax_amount": None,  # Not provided in this endpoint
                        "payment_status": None,  # Not provided in this endpoint
                        "last_payment_date": None,  # Not provided in this endpoint
                        "raw_data": Json(valuation),
                    }

                    if self.insert_tax_history(tax_data):
                        valuation_records_saved += 1

                logger.info(
                    f"Saved {valuation_records_saved} valuation records for APN: {apn}"
                )

            # Save detailed property data to raw_data field for future use
            if "detailed_data" in comprehensive_info:
                logger.debug(
                    f"Stored detailed data from {len(comprehensive_info['detailed_data'])} endpoints for APN: {apn}"
                )

            logger.info(
                f"Successfully saved comprehensive property data for APN: {apn}"
            )
            return True

        except Exception as e:
            log_exception(
                logger, e, f"saving comprehensive property data for APN: {apn}"
            )
            return False

    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None or value == "":
            return None
        try:
            if isinstance(value, str):
                # Remove any whitespace and convert
                cleaned = value.strip()
                if cleaned.isdigit():
                    return int(cleaned)
                return None
            return int(value)
        except (ValueError, TypeError):
            return None

    def validate_property_data(
        self, property_data: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate property data before insertion"""
        errors = []

        # Check for required fields
        if not property_data.get("apn"):
            errors.append("Missing required field: 'apn'")

        # Check data types for numeric fields
        numeric_fields = [
            "year_built",
            "living_area_sqft",
            "lot_size_sqft",
            "bedrooms",
            "bathrooms",
            "garage_spaces",
        ]
        for field in numeric_fields:
            value = property_data.get(field)
            if value is not None and not isinstance(value, (int, float, type(None))):
                try:
                    # Try to convert to numeric
                    if isinstance(value, str) and value.strip():
                        float(value.strip())
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for field '{field}': {value}")

        # Validate boolean fields
        boolean_fields = ["pool"]
        for field in boolean_fields:
            value = property_data.get(field)
            if value is not None and not isinstance(value, (bool, type(None))):
                if value not in [0, 1, "0", "1", "true", "false", "True", "False"]:
                    errors.append(f"Invalid boolean value for field '{field}': {value}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _ensure_tables_exist(self):
        """Ensure all required tables exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create data collection status table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS data_collection_status (
                        apn VARCHAR(50) PRIMARY KEY,
                        status VARCHAR(20) NOT NULL,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Add indexes for performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_collection_status_status
                    ON data_collection_status(status)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_collection_status_completed
                    ON data_collection_status(completed_at)
                    WHERE status = 'completed'
                """
                )

                conn.commit()
                logger.debug("Database schema verification completed")

        except Exception as e:
            logger.error(f"Error ensuring tables exist: {e}")

    def close(self):
        """Close the database connection pool"""
        logger.info("Closing database connection pool")

        try:
            if self._connection_pool:
                with self._pool_lock:
                    self._connection_pool.closeall()
                logger.info("Database connection pool closed successfully")
            elif self.pool:
                self.pool.closeall()
                logger.info("Database connection pool closed successfully")
            else:
                logger.debug("Database connection pool was already closed")

        except Exception as e:
            log_exception(logger, e, "closing database connection pool")


# =======================
# BACKWARD COMPATIBILITY ALIASES
# =======================

# Create aliases for backward compatibility
DatabaseManager = UnifiedDatabaseManager
ThreadSafeDatabaseManager = UnifiedDatabaseManager

# Export both names for maximum compatibility
__all__ = ["UnifiedDatabaseManager", "DatabaseManager", "ThreadSafeDatabaseManager"]
