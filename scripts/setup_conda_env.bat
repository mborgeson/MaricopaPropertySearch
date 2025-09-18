@echo off
title Setting up Conda Environment for Maricopa Property Search
echo ========================================
echo Setting up Conda Environment...
echo ========================================
echo.

:: Navigate to project directory
cd /d C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch

:: Check if conda is available
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Conda not found in PATH!
    echo Please install Anaconda/Miniconda first.
    echo Download from: https://www.anaconda.com/products/individual
    pause
    exit /b 1
)

:: Remove existing environment if it exists
echo Checking for existing environment...
call conda env list | findstr /C:"maricopa_property" >nul 2>nul
if %errorlevel% equ 0 (
    echo Found existing environment. Removing...
    call conda deactivate 2>nul
    call conda env remove -n maricopa_property -y
)

:: Create new environment
echo Creating new conda environment from environment.yml...
call conda env create -f environment.yml

if %errorlevel% neq 0 (
    echo ERROR: Failed to create conda environment!
    echo Please check environment.yml for errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Environment created successfully!
echo.
echo To activate the environment, run:
echo   conda activate maricopa_property
echo ========================================
pause