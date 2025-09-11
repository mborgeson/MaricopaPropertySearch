-- Maricopa Property Search Database Setup
-- Run this script as postgres user first to create database and user

-- Create database
CREATE DATABASE maricopa_properties;

-- Create user
CREATE USER property_user WITH PASSWORD 'Maricopa2024!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE maricopa_properties TO property_user;

-- Connect to the new database
\c maricopa_properties;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO property_user;