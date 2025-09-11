#!/usr/bin/env python
"""
Thread-Safe Database Manager
Enhanced database operations optimized for concurrent background data collection
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

from database_manager import DatabaseManager
from logging_config import get_logger

logger = get_logger(__name__)


class ThreadSafeDatabaseManager(DatabaseManager):
    """Enhanced database manager with thread-safe operations for background data collection"""
    
    def __init__(self, config_manager, min_connections=5, max_connections=20):
        """Initialize with connection pooling for concurrent operations"""
        
        # Get database configuration
        self.config = config_manager.get_database_config()
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        # Thread safety
        self._pool_lock = RLock()
        self._stats_lock = Lock()
        
        # Connection pool
        self._connection_pool = None
        
        # Performance tracking
        self._operation_stats = {
            'inserts': {'count': 0, 'total_time': 0.0, 'errors': 0},
            'selects': {'count': 0, 'total_time': 0.0, 'errors': 0},
            'updates': {'count': 0, 'total_time': 0.0, 'errors': 0}
        }
        
        # Initialize connection pool
        self._initialize_connection_pool()
        
        # Initialize database schema if needed
        self._ensure_tables_exist()
        
        logger.info(f"Thread-safe database manager initialized with pool size {min_connections}-{max_connections}")
    
    def _initialize_connection_pool(self):
        """Initialize the connection pool"""
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
                cursor_factory=RealDictCursor
            )
            
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with automatic cleanup"""
        conn = None
        try:
            with self._pool_lock:
                conn = self._connection_pool.getconn()
            
            # Set autocommit for better concurrent performance
            conn.autocommit = False
            yield conn
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                try:
                    with self._pool_lock:
                        self._connection_pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
    
    def _record_operation_stats(self, operation_type: str, duration: float, error: bool = False):
        """Record operation statistics"""
        with self._stats_lock:
            stats = self._operation_stats.get(operation_type, {'count': 0, 'total_time': 0.0, 'errors': 0})
            stats['count'] += 1
            stats['total_time'] += duration
            if error:
                stats['errors'] += 1
            self._operation_stats[operation_type] = stats
    
    def insert_property_safe(self, property_data: Dict[str, Any]) -> bool:
        """Thread-safe property insertion with conflict handling"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use upsert (INSERT ... ON CONFLICT) for thread safety
                sql = """
                INSERT INTO properties (
                    apn, owner_name, property_address, mailing_address,
                    legal_description, land_use_code, year_built, living_area_sqft,
                    lot_size_sqft, bedrooms, bathrooms, pool, garage_spaces, raw_data,
                    created_at, last_updated
                ) VALUES (
                    %(apn)s, %(owner_name)s, %(property_address)s, %(mailing_address)s,
                    %(legal_description)s, %(land_use_code)s, %(year_built)s, %(living_area_sqft)s,
                    %(lot_size_sqft)s, %(bedrooms)s, %(bathrooms)s, %(pool)s, %(garage_spaces)s, %(raw_data)s,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
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
                
                # Prepare data with JSON serialization for raw_data
                insert_data = property_data.copy()
                if 'raw_data' in insert_data and insert_data['raw_data']:
                    insert_data['raw_data'] = Json(insert_data['raw_data'])
                
                cursor.execute(sql, insert_data)
                conn.commit()
                
                duration = time.time() - start_time
                self._record_operation_stats('inserts', duration)
                
                logger.debug(f"Property inserted/updated for APN: {property_data.get('apn')}")
                return True
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats('inserts', duration, error=True)
            logger.error(f"Error inserting property {property_data.get('apn', 'unknown')}: {e}")
            return False
    
    def insert_tax_history_safe(self, tax_data: Dict[str, Any]) -> bool:
        """Thread-safe tax history insertion"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO tax_history (
                    apn, tax_year, assessed_value, limited_value, tax_amount,
                    payment_status, last_payment_date, raw_data, created_at
                ) VALUES (
                    %(apn)s, %(tax_year)s, %(assessed_value)s, %(limited_value)s, %(tax_amount)s,
                    %(payment_status)s, %(last_payment_date)s, %(raw_data)s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (apn, tax_year) DO UPDATE SET
                    assessed_value = COALESCE(EXCLUDED.assessed_value, tax_history.assessed_value),
                    limited_value = COALESCE(EXCLUDED.limited_value, tax_history.limited_value),
                    tax_amount = COALESCE(EXCLUDED.tax_amount, tax_history.tax_amount),
                    payment_status = COALESCE(EXCLUDED.payment_status, tax_history.payment_status),
                    last_payment_date = COALESCE(EXCLUDED.last_payment_date, tax_history.last_payment_date),
                    raw_data = COALESCE(EXCLUDED.raw_data, tax_history.raw_data)
                """
                
                # Prepare data
                insert_data = tax_data.copy()
                if 'raw_data' in insert_data and insert_data['raw_data']:
                    insert_data['raw_data'] = Json(insert_data['raw_data'])
                
                cursor.execute(sql, insert_data)
                conn.commit()
                
                duration = time.time() - start_time
                self._record_operation_stats('inserts', duration)
                
                logger.debug(f"Tax history inserted for APN: {tax_data.get('apn')}, year: {tax_data.get('tax_year')}")
                return True
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats('inserts', duration, error=True)
            logger.error(f"Error inserting tax history for {tax_data.get('apn', 'unknown')}: {e}")
            return False
    
    def insert_sales_history_safe(self, sales_data: Dict[str, Any]) -> bool:
        """Thread-safe sales history insertion"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO sales_history (
                    apn, sale_date, sale_price, seller_name, buyer_name,
                    deed_type, recording_number, created_at
                ) VALUES (
                    %(apn)s, %(sale_date)s, %(sale_price)s, %(seller_name)s, %(buyer_name)s,
                    %(deed_type)s, %(recording_number)s, CURRENT_TIMESTAMP
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
                self._record_operation_stats('inserts', duration)
                
                logger.debug(f"Sales history inserted for APN: {sales_data.get('apn')}, date: {sales_data.get('sale_date')}")
                return True
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats('inserts', duration, error=True)
            logger.error(f"Error inserting sales history for {sales_data.get('apn', 'unknown')}: {e}")
            return False
    
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
                    data_tuples.append((
                        record.get('apn'),
                        record.get('tax_year'),
                        record.get('assessed_value'),
                        record.get('limited_value'),
                        record.get('tax_amount'),
                        record.get('payment_status'),
                        record.get('last_payment_date'),
                        Json(record.get('raw_data', {}))
                    ))
                
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
                self._record_operation_stats('inserts', duration)
                
                logger.info(f"Bulk inserted {inserted_count} tax records in {duration:.2f}s")
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats('inserts', duration, error=True)
            logger.error(f"Error in bulk tax history insert: {e}")
            logger.debug(traceback.format_exc())
        
        return inserted_count
    
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
                    data_tuples.append((
                        record.get('apn'),
                        record.get('sale_date'),
                        record.get('sale_price'),
                        record.get('seller_name'),
                        record.get('buyer_name'),
                        record.get('deed_type'),
                        record.get('recording_number', f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}")
                    ))
                
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
                self._record_operation_stats('inserts', duration)
                
                logger.info(f"Bulk inserted {inserted_count} sales records in {duration:.2f}s")
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats('inserts', duration, error=True)
            logger.error(f"Error in bulk sales history insert: {e}")
            logger.debug(traceback.format_exc())
        
        return inserted_count
    
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
                        status['tax_records_count'] > 0 and
                        status.get('latest_tax_year', 0) >= datetime.now().year - 1
                    )
                    
                    has_recent_sales = (
                        status['sales_records_count'] > 0 and
                        status.get('latest_sale_date') and
                        status['latest_sale_date'] > (datetime.now().date() - timedelta(days=1825))  # 5 years
                    )
                    
                    status['data_complete'] = has_current_tax and has_recent_sales
                    status['needs_tax_collection'] = not has_current_tax
                    status['needs_sales_collection'] = not has_recent_sales
                    
                    duration = time.time() - start_time
                    self._record_operation_stats('selects', duration)
                    
                    return status
                else:
                    return {
                        'apn': apn,
                        'exists': False,
                        'tax_records_count': 0,
                        'sales_records_count': 0,
                        'data_complete': False,
                        'needs_tax_collection': True,
                        'needs_sales_collection': True
                    }
                    
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats('selects', duration, error=True)
            logger.error(f"Error getting data collection status for {apn}: {e}")
            return {
                'apn': apn,
                'error': str(e),
                'data_complete': False,
                'needs_tax_collection': True,
                'needs_sales_collection': True
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
                
                cursor.execute(sql, (current_year, five_years_ago, current_year, five_years_ago, limit))
                results = cursor.fetchall()
                
                duration = time.time() - start_time
                self._record_operation_stats('selects', duration)
                
                logger.info(f"Found {len(results)} APNs needing data collection")
                return [dict(row) for row in results]
                
        except Exception as e:
            duration = time.time() - start_time
            self._record_operation_stats('selects', duration, error=True)
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
    
    def mark_collection_completed(self, apn: str, success: bool, error_message: Optional[str] = None) -> bool:
        """Mark an APN collection as completed"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                status = 'completed' if success else 'failed'
                
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
    
    def get_database_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        with self._stats_lock:
            stats = {}
            
            # Calculate averages and rates
            for op_type, op_stats in self._operation_stats.items():
                if op_stats['count'] > 0:
                    avg_time = op_stats['total_time'] / op_stats['count']
                    error_rate = (op_stats['errors'] / op_stats['count']) * 100
                else:
                    avg_time = 0
                    error_rate = 0
                
                stats[op_type] = {
                    'count': op_stats['count'],
                    'average_time': avg_time,
                    'total_time': op_stats['total_time'],
                    'error_count': op_stats['errors'],
                    'error_rate_percent': error_rate
                }
            
            # Add connection pool stats
            if self._connection_pool:
                try:
                    with self._pool_lock:
                        # Get pool status (these methods may not be available in all versions)
                        stats['connection_pool'] = {
                            'min_connections': self.min_connections,
                            'max_connections': self.max_connections,
                            'status': 'active'
                        }
                except Exception as e:
                    stats['connection_pool'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return stats
    
    def _ensure_tables_exist(self):
        """Ensure all required tables exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create data collection status table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS data_collection_status (
                        apn VARCHAR(50) PRIMARY KEY,
                        status VARCHAR(20) NOT NULL,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Add indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_collection_status_status 
                    ON data_collection_status(status)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_collection_status_completed 
                    ON data_collection_status(completed_at) 
                    WHERE status = 'completed'
                """)
                
                conn.commit()
                logger.debug("Database schema verification completed")
                
        except Exception as e:
            logger.error(f"Error ensuring tables exist: {e}")
    
    def close(self):
        """Close the database connection pool"""
        if self._connection_pool:
            try:
                with self._pool_lock:
                    self._connection_pool.closeall()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False