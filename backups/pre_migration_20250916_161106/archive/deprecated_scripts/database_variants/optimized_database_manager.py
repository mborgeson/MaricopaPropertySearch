"""
Optimized Database Manager
Enhanced database operations with performance optimizations and advanced search capabilities
"""

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import ThreadedConnectionPool

from src.database_manager import DatabaseManager
from src.search_validator import SearchType, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    """Advanced search filters"""

    year_built_min: Optional[int] = None
    year_built_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    living_area_min: Optional[int] = None
    living_area_max: Optional[int] = None
    lot_size_min: Optional[int] = None
    lot_size_max: Optional[int] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    bathrooms_min: Optional[float] = None
    bathrooms_max: Optional[float] = None
    has_pool: Optional[bool] = None
    land_use_codes: Optional[List[str]] = None
    sort_by: str = "owner_name"
    sort_order: str = "ASC"


class OptimizedDatabaseManager(DatabaseManager):
    """Enhanced database manager with performance optimizations"""

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.query_cache = {}
        self.query_stats = {}
        self._init_query_optimization()

    def _init_query_optimization(self):
        """Initialize query optimization features"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Ensure we have necessary indexes
                self._ensure_optimized_indexes(cursor)

                # Update table statistics for query planner
                cursor.execute("ANALYZE properties, tax_history, sales_history;")
                conn.commit()

                logger.info("Database optimization initialized")
        except Exception as e:
            logger.error(f"Failed to initialize query optimization: {e}")

    def _ensure_optimized_indexes(self, cursor):
        """Ensure all performance indexes exist"""
        indexes = [
            # Composite indexes for common search patterns
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_owner_year ON properties(owner_name, year_built) WHERE owner_name IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_year ON properties(property_address, year_built) WHERE property_address IS NOT NULL",
            # Partial indexes for filtered searches
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_year_built ON properties(year_built) WHERE year_built IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_living_area ON properties(living_area_sqft) WHERE living_area_sqft IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_lot_size ON properties(lot_size_sqft) WHERE lot_size_sqft IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_pool ON properties(pool) WHERE pool = TRUE",
            # Value-based indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tax_history_assessed_value ON tax_history(assessed_value) WHERE assessed_value IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_history_sale_price ON sales_history(sale_price) WHERE sale_price IS NOT NULL",
            # Expression indexes for case-insensitive searches
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_owner_lower ON properties(LOWER(owner_name)) WHERE owner_name IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_lower ON properties(LOWER(property_address)) WHERE property_address IS NOT NULL",
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                logger.debug(
                    f"Index created/verified: {index_sql.split()[-1] if 'idx_' in index_sql else 'unknown'}"
                )
            except Exception as e:
                logger.warning(f"Index creation skipped (may already exist): {e}")

    def advanced_property_search(
        self,
        search_term: str,
        search_type: SearchType,
        filters: SearchFilters = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """Advanced property search with filtering and pagination"""

        if filters is None:
            filters = SearchFilters()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Build dynamic query based on search type and filters
                base_query, count_query, params = self._build_advanced_query(
                    search_term, search_type, filters, limit, offset
                )

                # Log query for performance monitoring
                start_time = time.time()

                # Get total count first
                cursor.execute(
                    count_query, params[:-2]
                )  # Exclude LIMIT and OFFSET params
                total_count = cursor.fetchone()[0]

                # Execute main query
                cursor.execute(base_query, params)
                results = [dict(row) for row in cursor.fetchall()]

                # Log performance
                query_time = time.time() - start_time
                self._log_query_performance(
                    search_type.value, query_time, len(results), total_count
                )

                return results, total_count

        except Exception as e:
            logger.error(
                f"Advanced search failed for {search_type.value} '{search_term}': {e}"
            )
            return [], 0

    def _build_advanced_query(
        self,
        search_term: str,
        search_type: SearchType,
        filters: SearchFilters,
        limit: int,
        offset: int,
    ) -> Tuple[str, str, List]:
        """Build optimized query with filters"""

        # Base SELECT and FROM clauses
        select_clause = """
        SELECT p.*, 
               t.tax_year as latest_tax_year,
               t.assessed_value as latest_assessed_value,
               t.tax_amount as latest_tax_amount,
               s.sale_date as latest_sale_date,
               s.sale_price as latest_sale_price
        """

        from_clause = """
        FROM properties p
        LEFT JOIN LATERAL (
            SELECT * FROM tax_history 
            WHERE apn = p.apn 
            ORDER BY tax_year DESC 
            LIMIT 1
        ) t ON true
        LEFT JOIN LATERAL (
            SELECT * FROM sales_history 
            WHERE apn = p.apn 
            ORDER BY sale_date DESC 
            LIMIT 1
        ) s ON true
        """

        # Build WHERE clause
        where_conditions = []
        params = []

        # Search term condition
        if search_type == SearchType.OWNER:
            where_conditions.append("LOWER(p.owner_name) LIKE LOWER(%s)")
            params.append(f"%{search_term}%")
        elif search_type == SearchType.ADDRESS:
            where_conditions.append("LOWER(p.property_address) LIKE LOWER(%s)")
            params.append(f"%{search_term}%")
        elif search_type == SearchType.APN:
            # Exact match for APN
            where_conditions.append("p.apn = %s")
            params.append(search_term)

        # Apply filters
        if filters.year_built_min is not None:
            where_conditions.append("p.year_built >= %s")
            params.append(filters.year_built_min)

        if filters.year_built_max is not None:
            where_conditions.append("p.year_built <= %s")
            params.append(filters.year_built_max)

        if filters.price_min is not None:
            where_conditions.append("t.assessed_value >= %s")
            params.append(filters.price_min)

        if filters.price_max is not None:
            where_conditions.append("t.assessed_value <= %s")
            params.append(filters.price_max)

        if filters.living_area_min is not None:
            where_conditions.append("p.living_area_sqft >= %s")
            params.append(filters.living_area_min)

        if filters.living_area_max is not None:
            where_conditions.append("p.living_area_sqft <= %s")
            params.append(filters.living_area_max)

        if filters.lot_size_min is not None:
            where_conditions.append("p.lot_size_sqft >= %s")
            params.append(filters.lot_size_min)

        if filters.lot_size_max is not None:
            where_conditions.append("p.lot_size_sqft <= %s")
            params.append(filters.lot_size_max)

        if filters.bedrooms_min is not None:
            where_conditions.append("p.bedrooms >= %s")
            params.append(filters.bedrooms_min)

        if filters.bedrooms_max is not None:
            where_conditions.append("p.bedrooms <= %s")
            params.append(filters.bedrooms_max)

        if filters.bathrooms_min is not None:
            where_conditions.append("p.bathrooms >= %s")
            params.append(filters.bathrooms_min)

        if filters.bathrooms_max is not None:
            where_conditions.append("p.bathrooms <= %s")
            params.append(filters.bathrooms_max)

        if filters.has_pool is not None:
            where_conditions.append("p.pool = %s")
            params.append(filters.has_pool)

        if filters.land_use_codes:
            placeholders = ",".join(["%s"] * len(filters.land_use_codes))
            where_conditions.append(f"p.land_use_code IN ({placeholders})")
            params.extend(filters.land_use_codes)

        # Combine WHERE conditions
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # ORDER BY clause
        valid_sort_columns = {
            "owner_name": "p.owner_name",
            "property_address": "p.property_address",
            "year_built": "p.year_built",
            "living_area": "p.living_area_sqft",
            "assessed_value": "t.assessed_value",
            "sale_price": "s.sale_price",
            "apn": "p.apn",
        }

        sort_column = valid_sort_columns.get(filters.sort_by, "p.owner_name")
        sort_order = "DESC" if filters.sort_order.upper() == "DESC" else "ASC"
        order_clause = f"ORDER BY {sort_column} {sort_order}"

        # LIMIT and OFFSET
        limit_clause = "LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Build final queries
        base_query = f"{select_clause} {from_clause} {where_clause} {order_clause} {limit_clause}"
        count_query = f"SELECT COUNT(*) {from_clause} {where_clause}"

        return base_query, count_query, params

    def get_property_suggestions(
        self, partial_term: str, search_type: SearchType, limit: int = 10
    ) -> List[str]:
        """Get property suggestions based on partial input"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if search_type == SearchType.OWNER:
                    sql = """
                    SELECT DISTINCT owner_name 
                    FROM properties 
                    WHERE LOWER(owner_name) LIKE LOWER(%s) 
                    AND owner_name IS NOT NULL
                    ORDER BY owner_name
                    LIMIT %s
                    """
                elif search_type == SearchType.ADDRESS:
                    sql = """
                    SELECT DISTINCT property_address 
                    FROM properties 
                    WHERE LOWER(property_address) LIKE LOWER(%s) 
                    AND property_address IS NOT NULL
                    ORDER BY property_address
                    LIMIT %s
                    """
                elif search_type == SearchType.APN:
                    sql = """
                    SELECT DISTINCT apn 
                    FROM properties 
                    WHERE apn LIKE %s
                    ORDER BY apn
                    LIMIT %s
                    """
                else:
                    return []

                cursor.execute(sql, (f"{partial_term}%", limit))
                results = cursor.fetchall()

                return [row[0] for row in results if row[0]]

        except Exception as e:
            logger.error(f"Failed to get suggestions for {search_type.value}: {e}")
            return []

    def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics for performance monitoring"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Search frequency by type
                cursor.execute(
                    """
                    SELECT search_type, COUNT(*) as search_count,
                           AVG(results_count) as avg_results
                    FROM search_history 
                    WHERE searched_at > NOW() - INTERVAL '%s days'
                    GROUP BY search_type
                    ORDER BY search_count DESC
                """,
                    (days,),
                )
                search_by_type = cursor.fetchall()

                # Most searched terms
                cursor.execute(
                    """
                    SELECT search_term, search_type, COUNT(*) as frequency
                    FROM search_history
                    WHERE searched_at > NOW() - INTERVAL '%s days'
                    GROUP BY search_term, search_type
                    ORDER BY frequency DESC
                    LIMIT 20
                """,
                    (days,),
                )
                popular_terms = cursor.fetchall()

                # Search performance (if we have timing data)
                cursor.execute(
                    """
                    SELECT DATE(searched_at) as date,
                           COUNT(*) as daily_searches,
                           AVG(results_count) as avg_results
                    FROM search_history
                    WHERE searched_at > NOW() - INTERVAL '%s days'
                    GROUP BY DATE(searched_at)
                    ORDER BY date
                """,
                    (days,),
                )
                daily_stats = cursor.fetchall()

                return {
                    "search_by_type": [dict(row) for row in search_by_type],
                    "popular_terms": [dict(row) for row in popular_terms],
                    "daily_stats": [dict(row) for row in daily_stats],
                    "query_performance": self.query_stats,
                }

        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {}

    def bulk_insert_properties(self, properties: List[Dict]) -> int:
        """Optimized bulk insert for properties"""
        if not properties:
            return 0

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Prepare data for bulk insert
                data_tuples = []
                for prop in properties:
                    data_tuples.append(
                        (
                            prop.get("apn"),
                            prop.get("owner_name"),
                            prop.get("property_address"),
                            prop.get("mailing_address"),
                            prop.get("legal_description"),
                            prop.get("land_use_code"),
                            prop.get("year_built"),
                            prop.get("living_area_sqft"),
                            prop.get("lot_size_sqft"),
                            prop.get("bedrooms"),
                            prop.get("bathrooms"),
                            prop.get("pool", False),
                            prop.get("garage_spaces"),
                            json.dumps(prop.get("raw_data", {})),
                        )
                    )

                # Use execute_batch for better performance
                sql = """
                INSERT INTO properties (
                    apn, owner_name, property_address, mailing_address,
                    legal_description, land_use_code, year_built, living_area_sqft,
                    lot_size_sqft, bedrooms, bathrooms, pool, garage_spaces, raw_data
                ) VALUES %s
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

                execute_batch(cursor, sql, data_tuples, page_size=1000)
                conn.commit()

                logger.info(f"Bulk inserted {len(properties)} properties")
                return len(properties)

        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            return 0

    def _log_query_performance(
        self, search_type: str, query_time: float, result_count: int, total_count: int
    ):
        """Log query performance for monitoring"""
        if search_type not in self.query_stats:
            self.query_stats[search_type] = {
                "total_queries": 0,
                "total_time": 0,
                "avg_time": 0,
                "min_time": float("inf"),
                "max_time": 0,
                "total_results": 0,
            }

        stats = self.query_stats[search_type]
        stats["total_queries"] += 1
        stats["total_time"] += query_time
        stats["avg_time"] = stats["total_time"] / stats["total_queries"]
        stats["min_time"] = min(stats["min_time"], query_time)
        stats["max_time"] = max(stats["max_time"], query_time)
        stats["total_results"] += result_count

        # Log slow queries
        if query_time > 2.0:  # Queries taking more than 2 seconds
            logger.warning(
                f"Slow query detected - {search_type}: {query_time:.2f}s, {result_count}/{total_count} results"
            )

    def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization operations"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                start_time = time.time()

                # Update table statistics
                cursor.execute("ANALYZE properties, tax_history, sales_history;")

                # Vacuum tables if needed (check table bloat)
                cursor.execute(
                    """
                    SELECT schemaname, tablename, n_dead_tup, n_live_tup,
                           CASE WHEN n_live_tup > 0 
                                THEN n_dead_tup::float / n_live_tup::float 
                                ELSE 0 END as bloat_ratio
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    AND n_dead_tup > 1000
                """
                )

                bloated_tables = cursor.fetchall()
                vacuum_results = []

                for table_info in bloated_tables:
                    table_name = table_info["tablename"]
                    bloat_ratio = table_info["bloat_ratio"]

                    if bloat_ratio > 0.1:  # More than 10% dead tuples
                        cursor.execute(f"VACUUM {table_name};")
                        vacuum_results.append(
                            {
                                "table": table_name,
                                "bloat_ratio": bloat_ratio,
                                "action": "vacuumed",
                            }
                        )

                conn.commit()
                optimization_time = time.time() - start_time

                return {
                    "duration": optimization_time,
                    "vacuum_results": vacuum_results,
                    "status": "completed",
                }

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return {"status": "failed", "error": str(e)}

    def get_property_statistics(self) -> Dict[str, Any]:
        """Get comprehensive property statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM properties")
                stats["total_properties"] = cursor.fetchone()[0]

                # Year built distribution
                cursor.execute(
                    """
                    SELECT 
                        CASE 
                            WHEN year_built IS NULL THEN 'Unknown'
                            WHEN year_built < 1950 THEN 'Before 1950'
                            WHEN year_built < 1980 THEN '1950-1979'
                            WHEN year_built < 2000 THEN '1980-1999'
                            WHEN year_built < 2020 THEN '2000-2019'
                            ELSE '2020+'
                        END as year_range,
                        COUNT(*) as count
                    FROM properties
                    GROUP BY year_range
                    ORDER BY year_range
                """
                )
                stats["year_distribution"] = [dict(row) for row in cursor.fetchall()]

                # Property value ranges
                cursor.execute(
                    """
                    SELECT 
                        CASE 
                            WHEN t.assessed_value IS NULL THEN 'Unknown'
                            WHEN t.assessed_value < 200000 THEN 'Under $200K'
                            WHEN t.assessed_value < 400000 THEN '$200K-$400K'
                            WHEN t.assessed_value < 600000 THEN '$400K-$600K'
                            WHEN t.assessed_value < 1000000 THEN '$600K-$1M'
                            ELSE 'Over $1M'
                        END as value_range,
                        COUNT(*) as count
                    FROM properties p
                    LEFT JOIN LATERAL (
                        SELECT * FROM tax_history 
                        WHERE apn = p.apn 
                        ORDER BY tax_year DESC 
                        LIMIT 1
                    ) t ON true
                    GROUP BY value_range
                    ORDER BY value_range
                """
                )
                stats["value_distribution"] = [dict(row) for row in cursor.fetchall()]

                # Land use codes
                cursor.execute(
                    """
                    SELECT land_use_code, COUNT(*) as count
                    FROM properties
                    WHERE land_use_code IS NOT NULL
                    GROUP BY land_use_code
                    ORDER BY count DESC
                    LIMIT 20
                """
                )
                stats["land_use_distribution"] = [
                    dict(row) for row in cursor.fetchall()
                ]

                return stats

        except Exception as e:
            logger.error(f"Failed to get property statistics: {e}")
            return {}
