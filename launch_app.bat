@echo off
title Maricopa Property Search
cls
echo ========================================
echo    Maricopa Property Search System
echo ========================================
echo.

:: Set project directory
set PROJECT_DIR=C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch
set ENV_NAME=maricopa_property
cd /d %PROJECT_DIR%

:: Initialize conda if needed
call conda info >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Conda not found or not initialized!
    echo Please run: conda init cmd.exe
    echo Then restart your command prompt and try again.
    pause
    exit /b 1
)

:: Check if conda environment exists
echo Checking for conda environment '%ENV_NAME%'...
call conda env list | findstr /C:"%ENV_NAME%" >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Conda environment '%ENV_NAME%' not found!
    echo.
    echo Creating environment from environment.yml...
    call conda env create -f environment.yml
    
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create environment!
        echo Please check environment.yml for errors.
        pause
        exit /b 1
    )
    echo Environment created successfully!
)

:: Activate environment with verification
echo Activating conda environment '%ENV_NAME%'...
call conda activate %ENV_NAME%

if %errorlevel% neq 0 (
    echo ERROR: Failed to activate environment!
    echo Please check your conda installation.
    pause
    exit /b 1
)

:: Verify environment activation
for /f "tokens=*" %%i in ('python -c "import os; print(os.environ.get('CONDA_DEFAULT_ENV', 'unknown'))"') do set ACTIVE_ENV=%%i
if not "%ACTIVE_ENV%"=="%ENV_NAME%" (
    echo WARNING: Environment activation may have failed!
    echo Expected: %ENV_NAME%
    echo Active: %ACTIVE_ENV%
    echo.
    echo Trying alternative activation method...
    call activate %ENV_NAME%
)

:: Check PostgreSQL service
echo Checking PostgreSQL service...
sc query postgresql-x64-14 | findstr RUNNING >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: PostgreSQL service not running!
    echo Starting PostgreSQL service...
    net start postgresql-x64-14
)

:: Set Python path
set PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%\src

:: Quick dependency check
echo.
echo Performing quick dependency check...
python -c "import PyQt5, psycopg2, pandas, requests, selenium; print('All core dependencies available')" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may be missing!
    echo Run scripts\verify_dependencies.py for detailed analysis.
    echo.
    set /p choice="Continue anyway? (y/N): "
    if /i not "%choice%"=="y" (
        echo Aborting startup.
        pause
        exit /b 1
    )
)

:: Launch application
echo.
echo Starting application...
echo ========================================
python src\maricopa_property_search.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to start!
    echo Check logs\maricopa_property.log for details.
)

pause