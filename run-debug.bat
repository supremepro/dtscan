@echo off
REM Verbose launcher: prints diagnostics, installs anything missing, then runs.
setlocal enableextensions
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"
set "VENV=%ROOT%\.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo [DTScan] No venv yet. Run run.bat first.
    pause
    exit /b 1
)

echo === Python ===
"%PY%" --version
echo.

echo === Installed packages ===
"%PY%" -m pip list
echo.

echo === Import check ===
"%PY%" -c "import sys; print('sys.path:'); [print(' ', p) for p in sys.path]"
"%PY%" -c "import PySide6, pdfplumber, dateutil; print('PySide6 OK'); print('pdfplumber OK'); print('dateutil OK')"

"%PY%" -c "import dtscan" 2>nul
if errorlevel 1 (
    echo dtscan: NOT installed
    echo.
    echo Installing DTScan package now...
    "%PY%" -m pip install -e "%ROOT%"
    if errorlevel 1 goto :install_failed
)
"%PY%" -c "import dtscan; print('dtscan OK ->', dtscan.__file__)"

echo.
echo === Launching DTScan ===
"%PY%" -m dtscan
echo.
echo Exit code: %ERRORLEVEL%
pause
exit /b 0

:install_failed
echo.
echo [DTScan] pip install -e . failed. See message above.
pause
exit /b 1
