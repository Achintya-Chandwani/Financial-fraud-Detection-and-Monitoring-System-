$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) { $ProjectDir = Get-Location }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " FraudShield AI - Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Start Backend in a visible window
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectDir'; Write-Host '--- FraudShield AI Backend ---' -ForegroundColor Green; .\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 2

# 2. Start Frontend in a visible window
Write-Host "[2/2] Starting Frontend Server on http://localhost:5500 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectDir'; Write-Host '--- FraudShield AI Frontend ---' -ForegroundColor Green; .\venv\Scripts\python.exe -m http.server 5500 --directory frontend"

Start-Sleep -Seconds 2

Write-Host "`nServices launched! Opening browser at http://localhost:5500 ..." -ForegroundColor Green
Start-Process "http://localhost:5500"

