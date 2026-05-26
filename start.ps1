# Finance Policy Assistant - Quick Start Script
# Usage: .\start.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   Finance Policy Assistant - Startup Script     " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check for .env file
$envFile = ".\backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: backend\.env file not found." -ForegroundColor Red
    Write-Host "Create it with your OpenAI API key:" -ForegroundColor Yellow
    Write-Host "  OPENAI_API_KEY=sk-..." -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Install dependencies if venv doesn't exist
$venvPath = ".\backend\.venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & "$venvPath\Scripts\pip.exe" install -r .\backend\requirements.txt
    Write-Host "Dependencies installed." -ForegroundColor Green
} else {
    Write-Host "Virtual environment found." -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting backend server on http://localhost:8000 ..." -ForegroundColor Cyan
Write-Host "Open frontend\index.html in your browser." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

Set-Location .\backend
& ".\.venv\Scripts\uvicorn.exe" app:app --host 0.0.0.0 --port 8000 --reload
