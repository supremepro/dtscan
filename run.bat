@echo off
REM Launch DTScan. Creates and provisions a venv on first run.
setlocal enableextensions
set ROOT=%~dp0
set VENV=%ROOT%.venv
set PY=%VENV%\Scripts\python.exe

REM 1) Locate a Python interpreter on PATH (python or py launcher).
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    set BOOT=python
) else (
    where py >nul 2>&1
    if %ERRORLEVEL%==0 (
        set BOOT=py -3
    ) else (
        echo [DTScan] Python 3.10+ not found on PATH.
        echo Install it from https://www.python.org/downloads/ and re-run.
        pause
        exit /b 1
    )
)

REM 2) Create the venv if missing.
if not exist "%PY%" (
    echo [DTScan] Creating virtual environment in "%VENV%"...
    %BOOT% -m venv "%VENV%" || goto :error
    "%PY%" -m pip install --upgrade pip || goto :error
    echo [DTScan] Installing dependencies...
    "%PY%" -m pip install -r "%ROOT%requirements.txt" || goto :error
    echo [DTScan] Installing app package...
    "%PY%" -m pip install -e "%ROOT%" || goto :error
)

REM 3) Launch with python.exe so any error is visible. Use pythonw later if you want it console-less.
"%PY%" -m dtscan
if %ERRORLEVEL% NEQ 0 goto :error
exit /b 0

:error
echo.
echo [DTScan] Startup failed. See the message above.
pause
exit /b 1
