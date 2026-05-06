@echo off
REM Diagnostic launcher: prints versions, verifies imports, then runs the app.
setlocal enableextensions
set ROOT=%~dp0
set VENV=%ROOT%.venv
set PY=%VENV%\Scripts\python.exe

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
"%PY%" -c "import dtscan; print('dtscan OK ->', dtscan.__file__)"
echo.
echo === Launching DTScan ===
"%PY%" -m dtscan
echo.
echo Exit code: %ERRORLEVEL%
pause
