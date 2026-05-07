@echo off
REM Launch DTScan. Self-healing: ensures venv, deps, and package are all
REM present before launch; installs whatever is missing.
setlocal enableextensions
set ROOT=%~dp0
cd /d "%ROOT%"
set VENV=%ROOT%.venv
set PY=%VENV%\Scripts\python.exe

REM 1) Locate a Python interpreter on PATH (python or py launcher).
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    set BOOT=python
    goto :have_python
)
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set BOOT=py -3
    goto :have_python
)
echo [DTScan] Python 3.10+ not found on PATH.
echo Install it from https://www.python.org/downloads/ and re-run.
pause
exit /b 1

:have_python

REM 2) Create venv if missing.
if not exist "%PY%" (
    echo [DTScan] Creating virtual environment...
    %BOOT% -m venv "%VENV%" || goto :error
    "%PY%" -m pip install --upgrade pip setuptools wheel || goto :error
)

REM 3) Verify third-party deps; install if any are missing.
"%PY%" -c "import PySide6, pdfplumber, dateutil" 2>nul
if errorlevel 1 (
    echo [DTScan] Installing dependencies...
    "%PY%" -m pip install -r "%ROOT%requirements.txt" || goto :error
)

REM 4) Verify the app package is installed in the venv (it lives under src/).
"%PY%" -c "import dtscan" 2>nul
if errorlevel 1 (
    echo [DTScan] Installing app package...
    "%PY%" -m pip install -e "%ROOT%" || goto :error
)

REM 5) Launch (with console so any error is visible).
"%PY%" -m dtscan
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo [DTScan] Startup failed. See the message above.
pause
exit /b 1
