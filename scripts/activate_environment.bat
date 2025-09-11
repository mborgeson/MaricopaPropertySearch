@echo off
title Maricopa Property Search - Environment Activation
cls

echo ========================================
echo    Environment Activation Script
echo ========================================
echo.

:: Set project directory
set PROJECT_DIR=C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch
set ENV_NAME=maricopa_property

:: Initialize conda in batch mode
call conda info >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Conda not found or not initialized!
    echo.
    echo Please run the following command in Command Prompt:
    echo conda init cmd.exe
    echo.
    echo Then restart your command prompt and try again.
    pause
    exit /b 1
)

:: Check if environment exists
echo Checking for environment '%ENV_NAME%'...
call conda env list | findstr /C:"%ENV_NAME%" >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Environment '%ENV_NAME%' not found!
    echo.
    echo Creating environment from environment.yml...
    cd /d %PROJECT_DIR%
    call conda env create -f environment.yml
    
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create environment!
        echo Please check environment.yml for errors.
        pause
        exit /b 1
    )
    echo Environment created successfully!
)

:: Activate environment
echo Activating environment '%ENV_NAME%'...
call conda activate %ENV_NAME%

if %errorlevel% neq 0 (
    echo ERROR: Failed to activate environment!
    pause
    exit /b 1
)

:: Verify activation
for /f "tokens=*" %%i in ('conda info --envs ^| findstr "*"') do set ACTIVE_ENV=%%i
echo Current environment: %ACTIVE_ENV%

:: Set Python path
set PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%\src

echo.
echo ========================================
echo Environment activated successfully!
echo Python Path: %PYTHONPATH%
echo ========================================
echo.

:: Keep window open for interactive use
cmd /k