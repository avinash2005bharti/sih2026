@echo off
title Stop Sovereign AI Workbench Services
echo ============================================================
echo   Stopping Sovereign AI Workbench Local Services
echo ============================================================

echo Stopping processes on ports 5173, 5000, 8000, 11434...
powershell -Command "Get-NetTCPConnection -LocalPort 5173, 5000, 8000, 11434 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

echo Services stopped.
pause
