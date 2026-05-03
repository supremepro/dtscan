@echo off
REM Build a single-file Windows executable using PyInstaller.
setlocal
set ROOT=%~dp0
set VENV=%ROOT%.venv

if not exist "%VENV%\Scripts\python.exe" (
    python -m venv "%VENV%" || goto :error
)

"%VENV%\Scripts\python.exe" -m pip install --upgrade pip || goto :error
"%VENV%\Scripts\python.exe" -m pip install -r "%ROOT%requirements-dev.txt" || goto :error

"%VENV%\Scripts\pyinstaller.exe" ^
    --noconfirm ^
    --windowed ^
    --name DTScan ^
    --collect-submodules pdfplumber ^
    --collect-data pdfplumber ^
    "%ROOT%src\dtscan\__main__.py" || goto :error

echo.
echo Build complete: dist\DTScan\DTScan.exe
exit /b 0

:error
echo Build failed.
exit /b 1
