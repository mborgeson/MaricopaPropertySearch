@echo off
title Testing Maricopa Property Search Installation
echo ========================================
echo Testing Installation...
echo ========================================
echo.

cd /d C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch

:: Activate environment
call conda activate maricopa_property

:: Run test script
python scripts\test_installation.py

pause