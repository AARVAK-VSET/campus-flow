@echo off
echo Starting CampusAI Backend...

REM Check if port 8000 is already in use
netstat -ano | findstr :8000 | findstr LISTENING > nul
if %errorlevel% == 0 (
    echo WARNING: Port 8000 is already in use by another process.
    echo Please close any other running instances of the backend.
    pause
    exit /b
)

REM Check if venv exists and activate it
if exist venv\Scripts\activate (
    call venv\Scripts\activate
) else (
    echo Note: Virtual environment not found. Using system python.
)
REM Run backend using uvicorn for auto-reload during development
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
