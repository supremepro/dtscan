@echo off
REM Launch DTScan from a venv. Creates the venv on first run.
setlocal
set ROOT=%~dp0
set VENV=%ROOT%.venv

if not exist "%VENV%\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv "%VENV%" || goto :error
    "%VENV%\Scripts\python.exe" -m pip install --upgrade pip || goto :error
    "%VENV%\Scripts\python.exe" -m pip install -r "%ROOT%requirements.txt" || goto :error
)

"%VENV%\Scripts\pythonw.exe" -m dtscan
exit /b 0

:error
echo Failed to set up environment.
exit /b 1
