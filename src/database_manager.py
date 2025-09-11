"""
Database Manager
Handles PostgreSQL database operations
"""

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import json

# Import centralized logging
from logging_config import get_logger, get_performance_logger, log_exception

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

class DatabaseManager:
    def __init__(self, config_manager):
        logger.info("Initializing Database Manager")
        
        self.config = config_manager.get_db_config()
        self.pool = None
        
        logger.debug(f"Database Configuration - Host: {self.config['host']}, Port: {self.config['port']}, Database: {self.config['database']}")
        
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """Initialize database connection pool"""
        logger.debug("Setting up database connection pool")
        
        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                cursor_factory=RealDictCursor
            )
            logger.info("Database connection pool initialized successfully")
            logger.debug("Connection pool configured with min=1, max=20 connections")
            
        except Exception as e:
            log_exception(logger, e, "initializing database connection pool")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        start_time = None
        
        try:
            start_time = perf_logger.logger.info
            logger.debug("Acquiring database connection from pool")
            connection = self.pool.getconn()
            logger.debug("Database connection acquired successfully")
            
            yield connection
            
        except Exception as e:
            if connection:
                connection.rollback()
                logger.debug("Database transaction rolled back due to error")
                
            log_exception(logger, e, "database operation")
            raise
            
        finally:
            if connection:
                logger.debug("Returning database connection to pool")
                self.pool.putconn(connection)
    
    @perf_logger.log_performance('test_connection')
    def test_connection(self) -> bool:
        """Test database connectivity"""
        logger.debug("Testing database connection")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and (result.get(0) == 1 or (hasattr(result, 'values') and 1 in result.values())):
                    logger.info("Database connection test successful")
                    return True
                else:
                    logger.error("Database connection test returned unexpected result")
                    return False
                    
        except Exception as e:
            log_exception(logger, e, "database connection test")
            return False
    
    # Property operations
    @perf_logger.log_database_operation('upsert', 'properties', 1)
    def insert_property(self, property_data: Dict[str, Any]) -> bool:
        """Insert or update property data"""
        apn = property_data.get('apn', 'unknown')
        logger.info(f"Inserting/updating property data for APN: {apn}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO properties (
                    apn, owner_name, property_address, mailing_address,
                    legal_description, land_use_code, year_built, living_area_sqft,
                    lot_size_sqft, bedrooms, bathrooms, pool, garage_spaces,
                    raw_data
                ) VALUES (
                    %(apn)s, %(owner_name)s, %(property_address)s, %(mailing_address)s,
                    %(legal_description)s, %(land_use_code)s, %(year_built)s, %(living_area_sqft)s,
                    %(lot_size_sqft)s, %(bedrooms)s, %(bathrooms)s, %(pool)s, %(garage_spaces)s,
                    %(raw_data)s
                )
                ON CONFLICT (apn) DO UPDATE SET
                    owner_name = EXCLUDED.owner_name,
                    property_address = EXCLUDED.property_address,
                    mailing_address = EXCLUDED.mailing_address,
                    legal_description = EXCLUDED.legal_description,
                    land_use_code = EXCLUDED.land_use_code,
                    year_built = EXCLUDED.year_built,
                    living_area_sqft = EXCLUDED.living_area_sqft,
                    lot_size_sqft = EXCLUDED.lot_size_sqft,
                    bedrooms = EXCLUDED.bedrooms,
                    bathrooms = EXCLUDED.bathrooms,
                    pool = EXCLUDED.pool,
                    garage_spaces = EXCLUDED.garage_spaces,
                    raw_data = EXCLUDED.raw_data,
                    last_updated = CURRENT_TIMESTAMP
                """
                
                cursor.execute(sql, property_data)
                conn.commit()
                logger.debug(f"Property data committed successfully for APN: {apn}")
                return True
                
        except Exception as e:
            log_exception(logger, e, f"inserting property data for APN: {apn}")
            return False
    
    @perf_logger.log_database_operation('search', 'properties', None)
    def search_properties_by_owner(self, owner_name: str, limit: int = 100) -> List[Dict]:
        """Search properties by owner name"""
        logger.info(f"Searching properties by owner: {owner_name} (limit: {limit})")
        
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
                
                logger.info(f"Found {len(results)} properties for owner: {owner_name}")
                logger.debug(f"DB_ANALYTICS: owner_search, query_time=measured, results={len(results)}, limit={limit}")
                
                return results
                
        except Exception as e:
            log_exception(logger, e, f"searching properties by owner: {owner_name}")
            return []
    
    @perf_logger.log_database_operation('search', 'properties', None)
    def search_properties_by_address(self, address: str, limit: int = 100) -> List[Dict]:
        """Search properties by address"""
        logger.info(f"Searching properties by address: {address} (limit: {limit})")
        
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
                
                logger.info(f"Found {len(results)} properties for address: {address}")
                logger.debug(f"DB_ANALYTICS: address_search, query_time=measured, results={len(results)}, limit={limit}")
                
                return results
                
        except Exception as e:
            log_exception(logger, e, f"searching properties by address: {address}")
            return []
    
    @perf_logger.log_database_operation('select', 'properties', 1)
    def get_property_by_apn(self, apn: str) -> Optional[Dict]:
        """Get property by APN"""
        logger.debug(f"Retrieving property data for APN: {apn}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = "SELECT * FROM property_current_view WHERE apn = %s"
                cursor.execute(sql, (apn,))
                
                result = cursor.fetchone()
                
                if result:
                    logger.debug(f"Property data found for APN: {apn}")
                    return dict(result)
                else:
                    logger.debug(f"No property data found for APN: {apn}")
                    return None
                
        except Exception as e:
            log_exception(logger, e, f"retrieving property data for APN: {apn}")
            return None
    
    # Tax history operations
    def insert_tax_history(self, tax_data: Dict[str, Any]) -> bool:
        """Insert tax history record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO tax_history (
                    apn, tax_year, assessed_value, limited_value,
                    tax_amount, payment_status, last_payment_date, raw_data
                ) VALUES (
                    %(apn)s, %(tax_year)s, %(assessed_value)s, %(limited_value)s,
                    %(tax_amount)s, %(payment_status)s, %(last_payment_date)s, %(raw_data)s
                )
                ON CONFLICT (apn, tax_year) DO UPDATE SET
                    assessed_value = EXCLUDED.assessed_value,
                    limited_value = EXCLUDED.limited_value,
                    tax_amount = EXCLUDED.tax_amount,
                    payment_status = EXCLUDED.payment_status,
                    last_payment_date = EXCLUDED.last_payment_date,
                    raw_data = EXCLUDED.raw_data
                """
                
                cursor.execute(sql, tax_data)
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to insert tax history for {tax_data.get('apn', 'unknown')}: {e}")
            return False
    
    def get_tax_history(self, apn: str) -> List[Dict]:
        """Get tax history for property"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                SELECT * FROM tax_history 
                WHERE apn = %s 
                ORDER BY tax_year DESC
                """
                
                cursor.execute(sql, (apn,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get tax history for {apn}: {e}")
            return []
    
    # Sales history operations
    def insert_sales_history(self, sales_data: Dict[str, Any]) -> bool:
        """Insert sales history record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO sales_history (
                    apn, sale_date, sale_price, seller_name,
                    buyer_name, deed_type, recording_number
                ) VALUES (
                    %(apn)s, %(sale_date)s, %(sale_price)s, %(seller_name)s,
                    %(buyer_name)s, %(deed_type)s, %(recording_number)s
                )
                """
                
                cursor.execute(sql, sales_data)
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to insert sales history for {sales_data.get('apn', 'unknown')}: {e}")
            return False
    
    def get_sales_history(self, apn: str) -> List[Dict]:
        """Get sales history for property"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                SELECT * FROM sales_history 
                WHERE apn = %s 
                ORDER BY sale_date DESC
                """
                
                cursor.execute(sql, (apn,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get sales history for {apn}: {e}")
            return []
    
    # Analytics
    @perf_logger.log_database_operation('insert', 'search_history', 1)
    def log_search(self, search_type: str, search_term: str, results_count: int, user_ip: str = None):
        """Log search for analytics"""
        logger.debug(f"Logging search analytics: {search_type} search for '{search_term}' with {results_count} results")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                INSERT INTO search_history (search_type, search_term, results_count, user_ip)
                VALUES (%s, %s, %s, %s)
                """
                
                cursor.execute(sql, (search_type, search_term, results_count, user_ip))
                conn.commit()
                
                logger.debug("Search analytics logged successfully")
                
        except Exception as e:
            log_exception(logger, e, f"logging search analytics for {search_type} search")
    
    @perf_logger.log_performance('get_database_stats')
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        logger.debug("Retrieving database statistics")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Property count
                cursor.execute("SELECT COUNT(*) FROM properties")
                stats['properties'] = cursor.fetchone()[0]
                
                # Tax records count
                cursor.execute("SELECT COUNT(*) FROM tax_history")
                stats['tax_records'] = cursor.fetchone()[0]
                
                # Sales records count
                cursor.execute("SELECT COUNT(*) FROM sales_history")
                stats['sales_records'] = cursor.fetchone()[0]
                
                # Recent searches
                cursor.execute("SELECT COUNT(*) FROM search_history WHERE searched_at > NOW() - INTERVAL '7 days'")
                stats['recent_searches'] = cursor.fetchone()[0]
                
                logger.info(f"Database statistics retrieved - Properties: {stats.get('properties', 0):,}, "
                          f"Tax Records: {stats.get('tax_records', 0):,}, "
                          f"Sales Records: {stats.get('sales_records', 0):,}")
                
                return stats
                
        except Exception as e:
            log_exception(logger, e, "retrieving database statistics")
            return {}
    
    def save_comprehensive_property_data(self, comprehensive_info: Dict[str, Any]) -> bool:
        """Save comprehensive property data including detailed information"""
        apn = comprehensive_info.get('apn', 'unknown')
        logger.info(f"Saving comprehensive property data for APN: {apn}")
        
        try:
            # Save basic property information
            basic_property_saved = self.insert_property(comprehensive_info)
            if not basic_property_saved:
                logger.warning(f"Failed to save basic property data for APN: {apn}")
                return False
            
            # Save valuation history if available
            valuation_records_saved = 0
            if 'valuation_history' in comprehensive_info:
                for valuation in comprehensive_info['valuation_history']:
                    tax_data = {
                        'apn': apn,
                        'tax_year': int(valuation.get('TaxYear', 0)),
                        'assessed_value': self._safe_int(valuation.get('FullCashValue', 0)),
                        'limited_value': self._safe_int(valuation.get('LimitedPropertyValue', '').strip()),
                        'tax_amount': None,  # Not provided in this endpoint
                        'payment_status': None,  # Not provided in this endpoint
                        'last_payment_date': None,  # Not provided in this endpoint
                        'raw_data': Json(valuation)
                    }
                    
                    if self.insert_tax_history(tax_data):
                        valuation_records_saved += 1
                
                logger.info(f"Saved {valuation_records_saved} valuation records for APN: {apn}")
            
            # Save detailed property data to raw_data field for future use
            if 'detailed_data' in comprehensive_info:
                logger.debug(f"Stored detailed data from {len(comprehensive_info['detailed_data'])} endpoints for APN: {apn}")
            
            logger.info(f"Successfully saved comprehensive property data for APN: {apn}")
            return True
            
        except Exception as e:
            log_exception(logger, e, f"saving comprehensive property data for APN: {apn}")
            return False
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None or value == '':
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
    
    def close(self):
        """Close database connection pool"""
        logger.info("Closing database connection pool")
        
        try:
            if self.pool:
                self.pool.closeall()
                logger.info("Database connection pool closed successfully")
            else:
                logger.debug("Database connection pool was already closed")
                
        except Exception as e:
            log_exception(logger, e, "closing database connection pool")