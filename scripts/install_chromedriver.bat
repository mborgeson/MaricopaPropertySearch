@echo off
title Installing ChromeDriver
echo ========================================
echo Installing ChromeDriver...
echo ========================================
echo.

cd /d C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch

:: Activate conda environment
call conda activate maricopa_property

if %errorlevel% neq 0 (
    echo ERROR: Failed to activate conda environment!
    echo Run setup_conda_env.bat first.
    pause
    exit /b 1
)

:: Run Python script
python scripts\install_chromedriver.py

pause