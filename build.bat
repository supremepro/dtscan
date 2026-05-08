@echo off
REM Build a single-file Windows executable using PyInstaller.
setlocal enableextensions
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "VENV=%ROOT%\.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    python -m venv "%VENV%" || goto :error
)

"%PY%" -m pip install --upgrade pip || goto :error
"%PY%" -m pip install -r "%ROOT%\requirements-dev.txt" || goto :error
"%PY%" -m pip install -e "%ROOT%" || goto :error

"%VENV%\Scripts\pyinstaller.exe" ^
    --noconfirm ^
    --windowed ^
    --name DTScan ^
    --collect-submodules pdfplumber ^
    --collect-data pdfplumber ^
    "%ROOT%\src\dtscan\__main__.py" || goto :error

echo.
echo Build complete: dist\DTScan\DTScan.exe
exit /b 0

:error
echo Build failed.
exit /b 1
