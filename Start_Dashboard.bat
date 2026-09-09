@echo off
title PowerStep System
echo ===================================================
echo Starting PowerStep System (Backend + Dashboard)
echo ===================================================
REM This assumes it's placed directly in your project root
REM (D:\main\PowerStep_New), next to main_system.py and
REM the dashboard_frontend\ folder — NOT inside a "backend" subfolder.

echo [1] Installing/checking dependencies...
python -m pip install -r requirements.txt

echo [2] Starting Backend (main_system.py) on port 8000...
start "PowerStep Backend" cmd /k "python main_system.py"

echo [3] Starting Dashboard frontend on port 5500...
cd dashboard_frontend
start "PowerStep Frontend" cmd /k "python -m http.server 5500"
cd ..

echo Waiting for servers to initialize...
timeout /t 4 >nul

echo [4] Opening Dashboard in your browser...
start http://localhost:5500/

echo Done. Backend: http://localhost:8000  |  Dashboard: http://localhost:5500
