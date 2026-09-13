# Sovereign AI Workbench - Start All Services
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🛡️  Starting Sovereign AI Workbench Services" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Docker Databases
Write-Host "[1/5] Checking Docker infrastructure..." -ForegroundColor Yellow
docker compose -f "$PSScriptRoot\docker-compose\docker-compose.yml" up -d mongodb valkey neo4j qdrant

# 2. Ollama
Write-Host "[2/5] Starting Local Ollama on port 11434..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'Sovereign - Ollama (11434)'; ollama serve"

Start-Sleep -Seconds 3

# 3. AI Service
Write-Host "[3/5] Starting FastAPI AI Service on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'Sovereign - AI Service (8000)'; Set-Location '$PSScriptRoot\AI-SERVICES'; python -m uvicorn main:app --port 8000"

Start-Sleep -Seconds 3

# 4. Backend
Write-Host "[4/5] Starting Express Backend on port 5000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'Sovereign - Backend (5000)'; Set-Location '$PSScriptRoot\BACKEND'; npm run dev"

Start-Sleep -Seconds 3

# 5. Frontend
Write-Host "[5/5] Starting React Frontend on port 5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'Sovereign - Frontend (5173)'; Set-Location '$PSScriptRoot\FRONTEND'; npm run dev"

Write-Host "============================================================" -ForegroundColor Green
Write-Host "✅ All 4 local services and Docker databases started!" -ForegroundColor Green
Write-Host "Frontend:  http://localhost:5173" -ForegroundColor Green
Write-Host "Backend:   http://localhost:5000" -ForegroundColor Green
Write-Host "AI-Service:http://localhost:8000" -ForegroundColor Green
Write-Host "Ollama:    http://localhost:11434" -ForegroundColor Green
Write-Host "Admin:     admin@sovereign.local / Admin@12345" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
