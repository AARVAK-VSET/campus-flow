@echo off
echo ===================================================
echo   🎓 CampusAI - Unified Startup Script
echo ===================================================
echo.

echo [1/2] Launching Backend Server...
start "CampusAI Backend" cmd /c "start_backend.bat"

echo [2/2] Launching Frontend Dashboard...
start "CampusAI Frontend" cmd /c "start_frontend.bat"

echo.
echo ---------------------------------------------------
echo ✅ Both services are launching in separate windows.
echo.
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo ---------------------------------------------------
echo.
echo Press any key to close this launcher (it won't stop the services).
pause > nul
