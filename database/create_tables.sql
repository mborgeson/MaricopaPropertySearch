-- Maricopa Property Search Table Creation
-- Run this as property_user after database creation

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Properties table
CREATE TABLE IF NOT EXISTS properties (
    apn VARCHAR(20) PRIMARY KEY,
    owner_name VARCHAR(255),
    property_address VARCHAR(500),
    mailing_address VARCHAR(500),
    legal_description TEXT,
    land_use_code VARCHAR(50),
    year_built INTEGER,
    living_area_sqft INTEGER,
    lot_size_sqft INTEGER,
    bedrooms INTEGER,
    bathrooms NUMERIC(3,1),
    pool BOOLEAN DEFAULT FALSE,
    garage_spaces INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tax history table
CREATE TABLE IF NOT EXISTS tax_history (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) REFERENCES properties(apn),
    tax_year INTEGER NOT NULL,
    assessed_value NUMERIC(12,2),
    limited_value NUMERIC(12,2),
    tax_amount NUMERIC(10,2),
    payment_status VARCHAR(50),
    last_payment_date DATE,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(apn, tax_year)
);

-- Sales history table
CREATE TABLE IF NOT EXISTS sales_history (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) REFERENCES properties(apn),
    sale_date DATE,
    sale_price NUMERIC(12,2),
    seller_name VARCHAR(255),
    buyer_name VARCHAR(255),
    deed_type VARCHAR(100),
    recording_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) REFERENCES properties(apn),
    document_type VARCHAR(100),
    recording_date DATE,
    url TEXT,
    parties JSONB,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search history table (for analytics)
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    search_type VARCHAR(50),
    search_term VARCHAR(255),
    results_count INTEGER,
    user_ip VARCHAR(45),
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_properties_owner ON properties USING gin(owner_name gin_trgm_ops);
CREATE INDEX idx_properties_address ON properties USING gin(property_address gin_trgm_ops);
CREATE INDEX idx_tax_history_apn_year ON tax_history(apn, tax_year);
CREATE INDEX idx_sales_history_apn ON sales_history(apn);
CREATE INDEX idx_sales_history_date ON sales_history(sale_date);
CREATE INDEX idx_documents_apn ON documents(apn);
CREATE INDEX idx_search_history_term ON search_history(search_term);

-- Create view for latest property data
CREATE OR REPLACE VIEW property_current_view AS
SELECT 
    p.*,
    t.tax_year as latest_tax_year,
    t.assessed_value as latest_assessed_value,
    t.tax_amount as latest_tax_amount,
    s.sale_date as latest_sale_date,
    s.sale_price as latest_sale_price
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
) s ON true;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO property_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO property_user;