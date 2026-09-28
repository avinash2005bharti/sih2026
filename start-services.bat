@echo off
title Sovereign AI Workbench Launcher
echo ========================================================
echo   Starting Sovereign AI Workbench
echo ========================================================
echo.

:: 1. Check Native Ollama
echo [1/4] Checking Native Ollama at http://127.0.0.1:11434...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Native Ollama is online and running.
) else (
    echo [WARNING] Ollama is not responding on http://127.0.0.1:11434.
    echo           Please ensure 'ollama serve' is running.
)
echo.

:: 2. Start MongoDB via Docker Compose
echo [2/4] Starting MongoDB Docker container...
docker volume create checkpointing_mongodb_data >nul 2>&1
docker compose -f docker-compose\docker-compose.yml up -d
echo.

:: 3. Start Python AI-SERVICES (FastAPI on Port 8000)
echo [3/4] Starting Python AI Service on http://127.0.0.1:8000...
start "AI-SERVICES (FastAPI :8000)" cmd /k "cd /d %~dp0AI-SERVICES && .\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo.

:: 4. Start Node.js BACKEND (Express on Port 5000)
echo [4/4] Starting Node.js Backend on http://localhost:5000...
start "BACKEND (Node.js :5000)" cmd /k "cd /d %~dp0BACKEND && node server.js"
echo.

:: 5. Start FRONTEND (Vite on Port 5173)
echo Starting Frontend UI on http://localhost:5173...
start "FRONTEND (Vite :5173)" cmd /k "cd /d %~dp0FRONTEND && npm run dev"
echo.

echo ========================================================
echo   All services have been launched!
echo   - Frontend:    http://localhost:5173
echo   - Backend:     http://localhost:5000
echo   - AI Service:  http://127.0.0.1:8000
echo   - Ollama:      http://127.0.0.1:11434 (Native)
echo   - MongoDB:     mongodb://admin:admin@localhost:27017
echo ========================================================
pause
