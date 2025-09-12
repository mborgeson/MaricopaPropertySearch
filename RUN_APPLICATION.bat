@echo off
REM ============================================================
REM    MARICOPA PROPERTY SEARCH - MASTER LAUNCHER
REM ============================================================

echo.
echo ============================================================
echo          MARICOPA PROPERTY SEARCH APPLICATION
echo                   Enhanced Version 2.0
echo ============================================================
echo.

REM Check if conda is available
where conda >nul 2>&1
if %errorlevel% == 0 (
    echo Activating conda environment: maricopa_property
    call conda activate maricopa_property
) else (
    echo Conda not found, using system Python
)

REM Run the master launcher
echo Starting application...
echo.
python RUN_APPLICATION.py

REM Pause to see any error messages
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo     APPLICATION EXITED WITH ERROR CODE: %errorlevel%
    echo ============================================================
    pause
) else (
    echo.
    echo ============================================================
    echo          APPLICATION CLOSED SUCCESSFULLY
    echo ============================================================
)