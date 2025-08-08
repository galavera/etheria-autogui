@echo off
setlocal enabledelayedexpansion

REM --- Always run from the folder this .bat lives in
pushd "%~dp0"

echo === Checking for Python 3.11 ===
REM Prefer the Python launcher if available (most reliable on Windows)
set "PY_CMD="

REM Try launcher: py -3.11
py -3.11 -V >nul 2>&1
if %errorlevel%==0 (
    set "PY_CMD=py -3.11"
) else (
    REM Try python directly (maybe already on PATH and is 3.11)
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do (
        set "FOUND_PY_VER=%%v"
    )
    echo Detected python version: !FOUND_PY_VER!
    echo !FOUND_PY_VER! | findstr /r "^3\.11\." >nul 2>&1
    if %errorlevel%==0 (
        set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    echo Python 3.11 not found. Installing per-user Python 3.11...
    set "PY_DL=%TEMP%\python-3.11.9-amd64.exe"
    REM Uses built-in curl on Windows 10+; -L follows redirects
    curl -L -o "%PY_DL%" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if errorlevel 1 (
        echo Failed to download the Python installer. Check your internet connection.
        pause
        exit /b 1
    )
    "%PY_DL%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1
    if errorlevel 1 (
        echo Python installer returned an error.
        pause
        exit /b 1
    )
    del "%PY_DL%" >nul 2>&1

    REM After install, the launcher should be present
    py -3.11 -V >nul 2>&1
    if %errorlevel%==0 (
        set "PY_CMD=py -3.11"
    ) else (
        REM Fallback to python (PATH updated for current user)
        set "PY_CMD=python"
    )
)

echo Using interpreter: %PY_CMD%
echo.

REM --- Create/refresh virtual environment
set "VENV_DIR=.venv"
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment in %VENV_DIR% ...
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM --- Activate venv
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM --- Upgrade pip (quietly) and install requirements if present
python -m pip install --upgrade pip >nul 2>&1
if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt ...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
) else (
    echo No requirements.txt found, skipping dependency install.
)

echo.
echo === Which script do you want to run? ===
echo   1 - main.py
echo   2 - alt.py
set /p choice="Enter 1 or 2: "

if "%choice%"=="1" (
    echo Running main.py ...
    python "main.py"
) else if "%choice%"=="2" (
    echo Running alt.py ...
    python "alt.py"
) else (
    echo Invalid choice. Exiting.
)

echo.
pause
endlocal
