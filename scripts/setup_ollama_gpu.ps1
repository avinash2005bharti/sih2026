# ==============================================================================
# Sovereign On-Premise Agentic AI Workbench — SIH 26117
# Local Ollama Model Setup for GPU Profile: NVIDIA RTX 2050 (4 GB VRAM)
# ==============================================================================
# This script verifies local Ollama availability and pulls only missing models.
# It does NOT re-download models that are already present.

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " SIH 26117 — RTX 2050 GPU Model Provisioning (4 GB VRAM Profile)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Verify Ollama CLI or Service is available
$OllamaUrl = "http://127.0.0.1:11434"
$OllamaAvailable = $false

try {
    $response = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    $OllamaAvailable = $true
    Write-Host "[OK] Ollama service detected running at $OllamaUrl" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama service not responding at $OllamaUrl. Checking 'ollama' command..." -ForegroundColor Yellow
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Write-Host "[INFO] 'ollama' command found. Starting Ollama serve or verifying..." -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] Ollama is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Please install Ollama from https://ollama.com and start the service." -ForegroundColor Red
        exit 1
    }
}

# 2. Get list of currently installed models
$InstalledModels = @()
try {
    $tags = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get
    if ($tags.models) {
        $InstalledModels = $tags.models | ForEach-Object { $_.name.ToLower().Trim() }
    }
} catch {
    # Fallback to CLI command
    $cliOutput = ollama list
    $InstalledModels = ($cliOutput | Select-Object -Skip 1) | ForEach-Object {
        $parts = $_ -split '\s+'
        if ($parts.Count -gt 0) { $parts[0].ToLower().Trim() }
    }
}

Write-Host "`nCurrently installed models in local Ollama:" -ForegroundColor DarkGray
foreach ($m in $InstalledModels) {
    Write-Host "  - $m" -ForegroundColor DarkGray
}

# 3. Define target RTX 2050 models
$TargetModels = @(
    @{ Role = "Task Classifier";        Model = "qwen3:0.6b";        Purpose = "Fast intent/task classification" },
    @{ Role = "Lightweight Router";     Model = "qwen3:1.7b";        Purpose = "Lightweight routing & simple reasoning" },
    @{ Role = "Main Planner / General"; Model = "qwen3:4b";          Purpose = "Planning, reasoning, synthesis & chat" },
    @{ Role = "Coding / Tool Agent";    Model = "qwen2.5-coder:3b";  Purpose = "Python, JS, scripts & tool execution" },
    @{ Role = "Vision Agent";           Model = "gemma3:4b";         Purpose = "Image/document/diagram understanding" },
    @{ Role = "Alternative Vision";     Model = "qwen2.5vl:3b";      Purpose = "Secondary vision model / fallback" },
    @{ Role = "Lightweight Vision FB";  Model = "moondream";         Purpose = "Low-resource vision fallback" },
    @{ Role = "Embedding Model";        Model = "nomic-embed-text";  Purpose = "RAG vector embeddings" }
)

Function Is-ModelInstalled($modelName) {
    $norm = $modelName.ToLower().Trim()
    foreach ($inst in $InstalledModels) {
        if ($inst -eq $norm -or $inst -eq "$norm`:latest" -or $norm -eq "$inst`:latest") {
            return $true
        }
    }
    return $false
}

Write-Host "`nProvisioning required models for RTX 2050 (4 GB VRAM):" -ForegroundColor Cyan

foreach ($item in $TargetModels) {
    $name = $item.Model
    $role = $item.Role
    $purpose = $item.Purpose

    if (Is-ModelInstalled $name) {
        Write-Host "  [SKIP] Model '$name' ($role) is ALREADY installed." -ForegroundColor Green
    } else {
        Write-Host "  [PULL] Downloading '$name' for $role ($purpose)..." -ForegroundColor Yellow
        try {
            ollama pull $name
            Write-Host "  [SUCCESS] Successfully pulled '$name'." -ForegroundColor Green
            # Update cache
            $InstalledModels += $name.ToLower().Trim()
        } catch {
            Write-Host "  [WARNING] Failed to pull '$name'. Ollama fallback chain will handle execution." -ForegroundColor Magenta
        }
    }
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host " RTX 2050 Model Provisioning Complete" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
