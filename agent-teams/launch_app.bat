@echo off
title IMP Agent Teams
echo.
echo  ====================================
echo   IMP Planner Agent Teams
echo  ====================================
echo.
echo  Starting application...
echo.

cd /d "%~dp0"

REM Check if streamlit is installed
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo  Installing required packages...
    pip install -r requirements.txt
)

echo.
echo  Opening browser at http://localhost:8501
echo  Press Ctrl+C to stop the server
echo.

start http://localhost:8501
python -m streamlit run app.py --server.port 8501 --server.headless true

pause
