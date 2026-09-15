@echo off
title Sovereign AI Workbench Launcher
echo ============================================================
echo   Sovereign On-Premise Agentic AI Workbench - Starting Services
echo ============================================================

:: 1. Ensure Docker databases are running
echo [1/5] Checking Docker infrastructure containers...
docker compose -f "%~dp0docker-compose\docker-compose.yml" up -d mongodb valkey neo4j qdrant

:: 2. Start Local Ollama
echo [2/5] Starting Local Ollama (port 11434)...
start "Sovereign - Ollama" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'Sovereign - Ollama (11434)'; ollama serve"

:: Wait 3 seconds for Ollama to initialize
timeout /t 3 /nobreak >nul

:: 3. Start Python FastAPI AI Service
echo [3/5] Starting AI Service (port 8000)...
start "Sovereign - AI Service" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'Sovereign - AI Service (8000)'; cd '%~dp0AI-SERVICES'; py -3 -m uvicorn main:app --port 8000"

:: Wait 3 seconds for AI Service to initialize
timeout /t 3 /nobreak >nul

:: 4. Start Node.js Express Backend
echo [4/5] Starting Backend (port 5000)...
start "Sovereign - Backend" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'Sovereign - Backend (5000)'; cd '%~dp0BACKEND'; npm run dev"

:: Wait 3 seconds for Backend to initialize
timeout /t 3 /nobreak >nul

:: 5. Start React Frontend
echo [5/5] Starting Frontend (port 5173)...
start "Sovereign - Frontend" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle = 'Sovereign - Frontend (5173)'; cd '%~dp0FRONTEND'; npm run dev"

echo.
echo ============================================================
echo   All services launched!
echo   Frontend:   http://localhost:5173
echo   Backend:    http://localhost:5000
echo   AI-Service: http://localhost:8000
echo   Ollama:     http://localhost:11434
echo   Admin:      admin@sovereign.local / Admin@12345
echo ============================================================
pause
