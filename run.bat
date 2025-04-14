@echo off
setlocal enabledelayedexpansion

:: Start Node.js in background
start "NodeJS" /B cmd /c "npm run start"
set "NODE_PID=!ERRORLEVEL!"

:: Start Python script in background
start "Python" /B cmd /c "python src\main.py"
set "PYTHON_PID=!ERRORLEVEL!"

:: Function to kill both processes (Ctrl+C)
:handle_exit
echo.
echo Terminating processes...
taskkill /PID %NODE_PID% /T /F >nul 2>&1
taskkill /PID %PYTHON_PID% /T /F >nul 2>&1
exit /B

:: Trap Ctrl+C (best effort)
:: Windows doesn't support Unix-style traps, but this helps
:: The choice loop below keeps script running
:wait_loop
choice /C YN /N /T 1 /D Y >nul
tasklist /FI "PID eq %NODE_PID%" | find "%NODE_PID%" >nul
if errorlevel 1 goto :handle_exit
tasklist /FI "PID eq %PYTHON_PID%" | find "%PYTHON_PID%" >nul
if errorlevel 1 goto :handle_exit
goto :wait_loop
