@echo off
setlocal EnableDelayedExpansion
title No Homers Club

:: Detect Python 3.11+
where python >nul 2>nul
if errorlevel 1 (
    echo [No Homers Club] Python not found. Install Python 3.11+ and ensure it is in PATH.
    exit /b 1
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>nul
if errorlevel 1 (
    echo [No Homers Club] Python 3.11+ required.
    exit /b 1
)

:: Create .venv if missing
if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv >nul 2>nul
    if errorlevel 1 (
        echo [No Homers Club] Failed to create .venv
        exit /b 1
    )
)

:: Activate venv and run
call .venv\Scripts\activate.bat
set PIP_DISABLE_PIP_VERSION_CHECK=1
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [No Homers Club] pip install failed
    exit /b 1
)
python run.py
endlocal
