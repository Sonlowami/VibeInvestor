@echo off
REM Launch script for VibeInvestor Gradio UI (Windows)

setlocal enabledelayedexpansion

echo 🚀 Starting VibeInvestor Gradio Interface...
echo.
echo Prerequisites check:

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)
echo ✓ Python found

REM Check project structure
if not exist "src\gradio_app.py" (
    echo ❌ Must run from VibeInvestor root directory
    exit /b 1
)
echo ✓ Project structure found

REM Check environment variables
if "!GOOGLE_API_KEY!"=="" (
    echo.
    echo ⚠️  WARNING: GOOGLE_API_KEY environment variable not set
    echo    Make sure you have a .env file with your API keys before running
)

if "!SEARCHAPI_KEY!"=="" (
    echo ⚠️  WARNING: SEARCHAPI_KEY environment variable not set
    echo    Make sure you have a .env file with your API keys before running
)

REM Check dependencies
echo.
echo Checking dependencies...
python -c "import gradio; import plotly" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -q -r requirements.txt
)
echo ✓ Dependencies ready

echo.
echo ════════════════════════════════════════════════════════════
echo         VibeInvestor UI is starting...
echo ════════════════════════════════════════════════════════════
echo.
echo 🌐 Open your browser to: http://localhost:7860
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the app
cd src
python gradio_app.py

endlocal
