@echo off
title PowerStep — DEMO MODE (Backup)
color 0A
echo.
echo  ==========================================
echo   ⚡ PowerStep DEMO MODE - احتياطي فقط
echo   لا يؤثر على المشروع الحقيقي
echo  ==========================================
echo.

echo [1] Starting DEMO Backend on port 8000...
start "PowerStep DEMO Backend" cmd /k "python demo_mode.py"

echo [2] Starting Dashboard Frontend on port 5500...
cd dashboard_frontend
start "PowerStep Frontend" cmd /k "python -m http.server 5500"
cd ..

echo Waiting for servers...
timeout /t 4 >nul

echo [3] Opening Dashboard...
start http://localhost:5500/

echo.
echo  ✅ DEMO MODE is running!
echo  ⚠️  Close these windows when done.
echo.
