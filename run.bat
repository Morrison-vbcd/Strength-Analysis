@echo off
setlocal
cd /d "%~dp0"

REM ============================================================
REM  Sector Relative Strength Tool - one-click launcher
REM  (Batch messages are ASCII-only on purpose: cmd.exe mangles
REM   UTF-8 Chinese in .bat files. App UI itself is Chinese.)
REM ============================================================

REM ---- Find Python: py launcher -> python on PATH -> user install dir ----
set "PYEXE="

py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%P in ('py -3 -c "import sys;print(sys.executable)"') do set "PYEXE=%%P"
)

if not defined PYEXE (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%P in ('python -c "import sys;print(sys.executable)"') do set "PYEXE=%%P"
    )
)

if not defined PYEXE (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set "PYEXE=%%D\python.exe"
    )
)

if not defined PYEXE (
    echo.
    echo [ERROR] Python not found.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and check "Add python.exe to PATH" during installation, then
    echo double-click run.bat again.
    echo.
    pause
    exit /b 1
)

echo Using Python: %PYEXE%

REM ---- Create virtual environment on first run ----
if not exist ".venv\Scripts\python.exe" (
    echo First run: creating virtual environment ...
    "%PYEXE%" -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM ---- Skip Streamlit first-run email prompt ----
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    mkdir "%USERPROFILE%\.streamlit" >nul 2>&1
    (echo [general]& echo email = "") > "%USERPROFILE%\.streamlit\credentials.toml"
)

REM ---- Install / update packages ----
echo Checking packages (first run may take 1-3 minutes) ...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package installation failed. Check your internet connection.
    pause
    exit /b 1
)

REM ---- Launch (Streamlit opens the browser automatically) ----
echo Starting app - browser will open at http://localhost:8501 ...
echo (Close this window to stop the app.)
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless false
pause
