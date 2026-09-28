# ==============================================================================
# Sovereign On-Premise Agentic AI Workbench — SIH 26117
# Local Ollama Model Setup for CPU Profile: CPU-Only Machines
# ==============================================================================
# This script verifies local Ollama availability and pulls only missing lightweight models.
# It does NOT pull heavy GPU models or re-download existing models.

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " SIH 26117 — CPU-Only Lightweight Model Provisioning Profile" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$OllamaUrl = "http://127.0.0.1:11434"

try {
    $response = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[OK] Ollama service running at $OllamaUrl" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama service not responding. Verifying 'ollama' command..." -ForegroundColor Yellow
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] Ollama is not installed or not in PATH." -ForegroundColor Red
        exit 1
    }
}

$InstalledModels = @()
try {
    $tags = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get
    if ($tags.models) {
        $InstalledModels = $tags.models | ForEach-Object { $_.name.ToLower().Trim() }
    }
} catch {
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

$CpuModels = @(
    @{ Role = "Task Classifier";     Model = "qwen2.5:0.5b";        Purpose = "Fast lightweight CPU intent classification" },
    @{ Role = "General / Planner";   Model = "qwen2.5:1.5b";        Purpose = "CPU-only general assistant & planning" },
    @{ Role = "Coding / Tool Agent"; Model = "qwen2.5-coder:1.5b";  Purpose = "CPU-only coding & scripting" },
    @{ Role = "Vision Agent";        Model = "moondream";           Purpose = "CPU lightweight vision" },
    @{ Role = "Embedding Model";     Model = "nomic-embed-text";    Purpose = "RAG vector embeddings" }
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

Write-Host "`nProvisioning lightweight models for CPU-Only profile:" -ForegroundColor Cyan

foreach ($item in $CpuModels) {
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
            $InstalledModels += $name.ToLower().Trim()
        } catch {
            Write-Host "  [WARNING] Failed to pull '$name': $_" -ForegroundColor Magenta
        }
    }
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host " CPU-Only Model Provisioning Complete" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
