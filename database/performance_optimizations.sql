-- Performance Optimizations for Maricopa Property Search
-- Run this script after the main database setup to add performance enhancements

-- Enable additional extensions for performance
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Enhanced indexes for search performance
-- Composite indexes for common search patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_owner_year 
    ON properties(owner_name, year_built) 
    WHERE owner_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_year 
    ON properties(property_address, year_built) 
    WHERE property_address IS NOT NULL;

-- Partial indexes for filtered searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_year_built_filtered 
    ON properties(year_built) 
    WHERE year_built IS NOT NULL AND year_built > 1900;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_living_area_filtered 
    ON properties(living_area_sqft) 
    WHERE living_area_sqft IS NOT NULL AND living_area_sqft > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_lot_size_filtered 
    ON properties(lot_size_sqft) 
    WHERE lot_size_sqft IS NOT NULL AND lot_size_sqft > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_pool_true 
    ON properties(apn) 
    WHERE pool = TRUE;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_bedrooms_filtered 
    ON properties(bedrooms) 
    WHERE bedrooms IS NOT NULL AND bedrooms > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_bathrooms_filtered 
    ON properties(bathrooms) 
    WHERE bathrooms IS NOT NULL AND bathrooms > 0;

-- Value-based indexes for tax and sales data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tax_history_assessed_value_filtered 
    ON tax_history(assessed_value, apn, tax_year) 
    WHERE assessed_value IS NOT NULL AND assessed_value > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_history_sale_price_filtered 
    ON sales_history(sale_price, apn, sale_date) 
    WHERE sale_price IS NOT NULL AND sale_price > 0;

-- Expression indexes for case-insensitive searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_owner_lower 
    ON properties(LOWER(owner_name)) 
    WHERE owner_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_address_lower 
    ON properties(LOWER(property_address)) 
    WHERE property_address IS NOT NULL;

-- Multi-column indexes for complex filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_comprehensive 
    ON properties(owner_name, year_built, living_area_sqft, bedrooms, bathrooms) 
    WHERE owner_name IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_value_search 
    ON properties(apn, year_built, living_area_sqft, lot_size_sqft, bedrooms, bathrooms, pool);

-- Indexes for search analytics and history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_history_analytics 
    ON search_history(search_type, searched_at, results_count);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_history_term_type 
    ON search_history(search_term, search_type, searched_at);

-- Optimize the property_current_view with materialized view for better performance
DROP VIEW IF EXISTS property_current_view;

CREATE MATERIALIZED VIEW property_current_view AS
SELECT 
    p.*,
    t.tax_year as latest_tax_year,
    t.assessed_value as latest_assessed_value,
    t.tax_amount as latest_tax_amount,
    s.sale_date as latest_sale_date,
    s.sale_price as latest_sale_price
FROM properties p
LEFT JOIN LATERAL (
    SELECT tax_year, assessed_value, tax_amount 
    FROM tax_history 
    WHERE apn = p.apn 
    ORDER BY tax_year DESC 
    LIMIT 1
) t ON true
LEFT JOIN LATERAL (
    SELECT sale_date, sale_price
    FROM sales_history 
    WHERE apn = p.apn 
    ORDER BY sale_date DESC 
    LIMIT 1
) s ON true;

-- Create indexes on the materialized view
CREATE UNIQUE INDEX idx_property_current_view_apn ON property_current_view(apn);
CREATE INDEX idx_property_current_view_owner ON property_current_view USING gin(owner_name gin_trgm_ops);
CREATE INDEX idx_property_current_view_address ON property_current_view USING gin(property_address gin_trgm_ops);
CREATE INDEX idx_property_current_view_year ON property_current_view(year_built) WHERE year_built IS NOT NULL;
CREATE INDEX idx_property_current_view_value ON property_current_view(latest_assessed_value) WHERE latest_assessed_value IS NOT NULL;

-- Function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_property_current_view()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY property_current_view;
END;
$$ LANGUAGE plpgsql;

-- Create a function to update table statistics
CREATE OR REPLACE FUNCTION update_search_statistics()
RETURNS void AS $$
BEGIN
    -- Update table statistics for query planner
    ANALYZE properties;
    ANALYZE tax_history;
    ANALYZE sales_history;
    ANALYZE search_history;
    
    -- Refresh materialized view
    PERFORM refresh_property_current_view();
    
    RAISE NOTICE 'Database statistics updated and materialized view refreshed';
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to refresh statistics (requires pg_cron extension)
-- This would typically be run by a cron job or scheduled task
-- SELECT cron.schedule('update-search-stats', '0 2 * * *', 'SELECT update_search_statistics();');

-- Add constraints for data integrity
ALTER TABLE properties ADD CONSTRAINT check_year_built_reasonable 
    CHECK (year_built IS NULL OR (year_built >= 1800 AND year_built <= EXTRACT(YEAR FROM CURRENT_DATE) + 5));

ALTER TABLE properties ADD CONSTRAINT check_living_area_positive 
    CHECK (living_area_sqft IS NULL OR living_area_sqft > 0);

ALTER TABLE properties ADD CONSTRAINT check_lot_size_positive 
    CHECK (lot_size_sqft IS NULL OR lot_size_sqft > 0);

ALTER TABLE properties ADD CONSTRAINT check_bedrooms_reasonable 
    CHECK (bedrooms IS NULL OR (bedrooms >= 0 AND bedrooms <= 50));

ALTER TABLE properties ADD CONSTRAINT check_bathrooms_reasonable 
    CHECK (bathrooms IS NULL OR (bathrooms >= 0 AND bathrooms <= 50));

ALTER TABLE tax_history ADD CONSTRAINT check_tax_year_reasonable 
    CHECK (tax_year >= 1900 AND tax_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1);

ALTER TABLE tax_history ADD CONSTRAINT check_assessed_value_positive 
    CHECK (assessed_value IS NULL OR assessed_value >= 0);

ALTER TABLE tax_history ADD CONSTRAINT check_tax_amount_positive 
    CHECK (tax_amount IS NULL OR tax_amount >= 0);

ALTER TABLE sales_history ADD CONSTRAINT check_sale_price_positive 
    CHECK (sale_price IS NULL OR sale_price > 0);

-- Performance monitoring views
CREATE OR REPLACE VIEW search_performance_summary AS
SELECT 
    search_type,
    COUNT(*) as total_searches,
    AVG(results_count) as avg_results,
    MIN(results_count) as min_results,
    MAX(results_count) as max_results,
    DATE_TRUNC('day', searched_at) as search_date,
    COUNT(*) FILTER (WHERE results_count = 0) as zero_result_searches
FROM search_history
WHERE searched_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY search_type, DATE_TRUNC('day', searched_at)
ORDER BY search_date DESC, total_searches DESC;

CREATE OR REPLACE VIEW popular_search_terms AS
SELECT 
    search_term,
    search_type,
    COUNT(*) as frequency,
    AVG(results_count) as avg_results,
    MAX(searched_at) as last_searched
FROM search_history
WHERE searched_at >= CURRENT_DATE - INTERVAL '90 days'
    AND LENGTH(TRIM(search_term)) >= 2
GROUP BY search_term, search_type
HAVING COUNT(*) >= 2
ORDER BY frequency DESC, last_searched DESC
LIMIT 100;

-- Cache management table for application-level caching
CREATE TABLE IF NOT EXISTS cache_entries (
    cache_key VARCHAR(64) PRIMARY KEY,
    search_type VARCHAR(20) NOT NULL,
    search_term VARCHAR(255) NOT NULL,
    filters_hash VARCHAR(64),
    result_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_entries_expires ON cache_entries(expires_at);
CREATE INDEX idx_cache_entries_search ON cache_entries(search_type, search_term);
CREATE INDEX idx_cache_entries_last_accessed ON cache_entries(last_accessed);

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get cache statistics
CREATE OR REPLACE FUNCTION get_cache_stats()
RETURNS TABLE(
    total_entries INTEGER,
    expired_entries INTEGER,
    size_mb NUMERIC,
    avg_access_count NUMERIC,
    most_popular_term TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_entries,
        COUNT(*) FILTER (WHERE expires_at < CURRENT_TIMESTAMP)::INTEGER as expired_entries,
        ROUND(pg_total_relation_size('cache_entries')::NUMERIC / (1024*1024), 2) as size_mb,
        ROUND(AVG(access_count), 2) as avg_access_count,
        (SELECT search_term FROM cache_entries ORDER BY access_count DESC LIMIT 1) as most_popular_term
    FROM cache_entries;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions for new objects
GRANT ALL ON ALL TABLES IN SCHEMA public TO property_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO property_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO property_user;

-- Initial refresh of materialized view
REFRESH MATERIALIZED VIEW property_current_view;

-- Update statistics
SELECT update_search_statistics();

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Performance optimizations completed successfully!';
    RAISE NOTICE 'Indexes created, materialized view refreshed, and statistics updated.';
    RAISE NOTICE 'Run "SELECT * FROM search_performance_summary;" to monitor search performance.';
END;
$$;