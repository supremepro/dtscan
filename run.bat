@echo off
REM Launch DTScan. Self-healing: ensures venv, deps, and package are present.
REM Structured as labelled subroutines to avoid cmd.exe parsing issues with
REM parentheses in folder paths (e.g. "Downloads\dtscan(1)\...").
setlocal enableextensions
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "VENV=%ROOT%.venv"
set "PY=%VENV%\Scripts\python.exe"
set "BOOT="

call :find_python
if errorlevel 1 goto :no_python

if not exist "%PY%" call :create_venv
if errorlevel 1 goto :error

call :ensure_deps
if errorlevel 1 goto :error

call :ensure_package
if errorlevel 1 goto :error

"%PY%" -m dtscan
if errorlevel 1 goto :error
exit /b 0


:find_python
where python >nul 2>&1
if not errorlevel 1 goto :found_python_cmd
where py >nul 2>&1
if not errorlevel 1 goto :found_py_launcher
exit /b 1
:found_python_cmd
set "BOOT=python"
exit /b 0
:found_py_launcher
set "BOOT=py -3"
exit /b 0


:create_venv
echo [DTScan] Creating virtual environment...
%BOOT% -m venv "%VENV%"
if errorlevel 1 exit /b 1
"%PY%" -m pip install --upgrade pip setuptools wheel
exit /b %ERRORLEVEL%


:ensure_deps
"%PY%" -c "import PySide6, pdfplumber, dateutil" 2>nul
if not errorlevel 1 exit /b 0
echo [DTScan] Installing dependencies...
"%PY%" -m pip install -r "%ROOT%requirements.txt"
exit /b %ERRORLEVEL%


:ensure_package
"%PY%" -c "import dtscan" 2>nul
if not errorlevel 1 exit /b 0
echo [DTScan] Installing DTScan package...
"%PY%" -m pip install -e "%ROOT%"
exit /b %ERRORLEVEL%


:no_python
echo [DTScan] Python 3.10+ not found on PATH.
echo Install it from https://www.python.org/downloads/ and re-run.
pause
exit /b 1

:error
echo.
echo [DTScan] Startup failed. See the message above.
pause
exit /b 1
