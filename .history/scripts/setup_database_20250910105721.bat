@echo off
title Setting up PostgreSQL Database
echo ========================================
echo Setting up PostgreSQL Database...
echo ========================================
echo.

set PGPASSWORD=Wildcats777!!
set DB_DIR=C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch\database

:: Check if PostgreSQL is installed
where psql >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL not found in PATH!
    echo Please install PostgreSQL first.
    echo.
    pause
    exit /b 1
)

:: Create database and user
echo Creating database and user...
psql -U postgres -f "%DB_DIR%\database_setup.sql"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create database!
    echo Make sure PostgreSQL service is running.
    pause
    exit /b 1
)

:: Create tables
echo.
echo Creating tables...
set PGPASSWORD=Wildcats777!!
psql -U property_user -d maricopa_properties -f "%DB_DIR%\create_tables.sql"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create tables!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Database setup completed successfully!
echo.
echo Database: maricopa_properties
echo User: property_user
echo Password: Wildcats777!!
echo ========================================
pause