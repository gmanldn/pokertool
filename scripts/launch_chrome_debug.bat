@echo off
REM Launch Chrome with Remote Debugging for Poker Tool
REM Usage: launch_chrome_debug.bat [port]

setlocal EnableDelayedExpansion

REM Set default port
set PORT=%1
if "%PORT%"=="" set PORT=9222

set BETFAIR_URL=https://poker-com-ngm.bfcdl.com/poker
set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
set PROFILE_DIR=%TEMP%\chrome-debug-profile

echo ==========================================
echo Chrome Remote Debugging Launcher
echo ==========================================
echo.
echo Port: %PORT%
echo URL: %BETFAIR_URL%
echo.

REM Check if Chrome exists
if not exist "%CHROME_PATH%" (
    echo X Chrome not found at: %CHROME_PATH%
    echo.
    echo Please install Chrome or update CHROME_PATH in this script
    echo Common locations:
    echo   C:\Program Files\Google\Chrome\Application\chrome.exe
    echo   C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
    pause
    exit /b 1
)

REM Check if port is already in use
netstat -ano | findstr ":%PORT% " > nul
if %ERRORLEVEL% equ 0 (
    echo Warning: Port %PORT% may already be in use
    echo.
    set /p KILL="Kill the process and continue? (y/n) "
    if /i "!KILL!"=="y" (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% "') do (
            taskkill /F /PID %%a > nul 2>&1
            echo Killed process %%a
        )
        timeout /t 1 > nul
    ) else (
        echo Aborted
        exit /b 1
    )
)

REM Launch Chrome
echo Launching Chrome with remote debugging...
echo.

start "" "%CHROME_PATH%" ^
    --remote-debugging-port=%PORT% ^
    --user-data-dir="%PROFILE_DIR%" ^
    "%BETFAIR_URL%"

REM Wait for Chrome to start
timeout /t 2 > nul

echo Chrome launched successfully!
echo.
echo Remote debugging: http://localhost:%PORT%
echo.
echo Next steps:
echo   1. Log in to Betfair in the Chrome window
echo   2. Join a poker table
echo   3. Run the poker tool GUI:
echo      python run_gui.py
echo   4. Go to the LiveTable tab
echo.
echo You should see: Lightning CDP (^< 20ms) in the status
echo.
echo To test CDP connection:
echo   python test_table_capture_diagnostic.py --live --cdp
echo.

pause
