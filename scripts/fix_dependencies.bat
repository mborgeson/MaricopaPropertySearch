@echo off
title Maricopa Property Search - Fix Dependencies
cls
echo ========================================
echo    Dependency Fix Script
echo ========================================
echo.

:: Set project directory and environment
set PROJECT_DIR=C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch
set ENV_NAME=maricopa_property
cd /d %PROJECT_DIR%

:: Activate environment
echo Activating environment %ENV_NAME%...
call conda activate %ENV_NAME%

if %errorlevel% neq 0 (
    echo ERROR: Could not activate environment!
    echo Please run scripts\setup_conda_env.bat first.
    pause
    exit /b 1
)

echo.
echo Installing/updating core dependencies...
echo ========================================

:: Install psycopg2 (both conda and pip versions)
echo Installing PostgreSQL adapter...
call conda install -c conda-forge psycopg2 -y
if %errorlevel% neq 0 (
    echo Conda install failed, trying pip...
    pip install psycopg2-binary --upgrade
)

:: Install PyQt5
echo Installing PyQt5...
call conda install -c conda-forge pyqt -y
if %errorlevel% neq 0 (
    echo Conda install failed, trying pip...
    pip install PyQt5 --upgrade
)

:: Install other core packages
echo Installing other core packages...
call conda install -c conda-forge pandas numpy matplotlib requests selenium beautifulsoup4 lxml openpyxl python-dotenv sqlalchemy -y

:: Install pip-only packages
echo Installing pip-specific packages...
pip install webdriver-manager pytest-qt pyqtgraph --upgrade

echo.
echo ========================================
echo Dependency installation complete!
echo.

:: Run verification
echo Running dependency verification...
python scripts\verify_dependencies.py

echo.
echo If all tests passed, you can now run launch_app.bat
pause