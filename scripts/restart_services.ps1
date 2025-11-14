# ================================================================
# Facebook/TikTok Automation - Windows PowerShell Startup Script
# ================================================================
# This script starts both backend (FastAPI) and frontend (React) natively on Windows
# Usage: powershell -ExecutionPolicy Bypass -File scripts/restart_services.ps1
# ================================================================

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Facebook/TikTok Automation Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ================================================================
# 1. STOP EXISTING SERVICES
# ================================================================
Write-Host "🛑 Stopping existing services..." -ForegroundColor Yellow

# Kill processes on port 8000 (backend)
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    $port8000 | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

# Kill processes on port 3000 (frontend)
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    $port3000 | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

# Kill by process name as backup
Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*python*" -and $_.CommandLine -like "*app.main*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.ProcessName -eq "node" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "   ✓ Stopped existing processes" -ForegroundColor Green
Start-Sleep -Seconds 2

# ================================================================
# 2. SETUP PYTHON ENVIRONMENT
# ================================================================
Write-Host ""
Write-Host "🐍 Setting up Python environment..." -ForegroundColor Yellow

$VENV_PATH = Join-Path $PROJECT_ROOT ".venv"

# Create venv if it doesn't exist
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "   Creating virtual environment..." -ForegroundColor Gray
    python -m venv $VENV_PATH
}

# Activate virtual environment
$ACTIVATE_SCRIPT = Join-Path $VENV_PATH "Scripts\Activate.ps1"
if (Test-Path $ACTIVATE_SCRIPT) {
    & $ACTIVATE_SCRIPT
    Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to find activation script at: $ACTIVATE_SCRIPT" -ForegroundColor Red
    exit 1
}

# Install/update dependencies if needed
$DEP_MARKER = Join-Path $VENV_PATH ".dependencies_installed"
if (-not (Test-Path $DEP_MARKER)) {
    Write-Host "   Installing Python dependencies..." -ForegroundColor Gray
    pip install -q uvicorn fastapi sqlalchemy alembic psycopg2-binary python-dotenv cryptography httpx pydantic-settings redis python-multipart
    New-Item -Path $DEP_MARKER -ItemType File -Force | Out-Null
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ✓ Dependencies already installed" -ForegroundColor Green
}

# Always ensure python-multipart is installed
$multipartCheck = pip show python-multipart 2>$null
if (-not $multipartCheck) {
    pip install -q python-multipart
}

# ================================================================
# 3. CREATE LOG DIRECTORY
# ================================================================
$LOG_DIR = Join-Path $PROJECT_ROOT ".logs"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -Path $LOG_DIR -ItemType Directory | Out-Null
}

# ================================================================
# 4. CHECK DATABASE CONNECTION
# ================================================================
Write-Host ""
Write-Host "🗄️  Checking database connection..." -ForegroundColor Yellow

# Try to connect to PostgreSQL
$pgCheck = Test-NetConnection -ComputerName localhost -Port 5432 -ErrorAction SilentlyContinue -WarningAction SilentlyContinue
if ($pgCheck.TcpTestSucceeded) {
    Write-Host "   ✓ PostgreSQL is running on localhost:5432" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  PostgreSQL may not be running on localhost:5432" -ForegroundColor Red
    Write-Host "   Backend may fail to start if database is not available" -ForegroundColor Red
}

# ================================================================
# 5. START BACKEND SERVICE
# ================================================================
Write-Host ""
Write-Host "🚀 Starting FastAPI backend..." -ForegroundColor Yellow

Set-Location $PROJECT_ROOT

$BACKEND_LOG = Join-Path $LOG_DIR "backend.log"

# Start backend in new window with log redirection
$backendJob = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
    -RedirectStandardOutput $BACKEND_LOG `
    -RedirectStandardError $BACKEND_LOG `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 5

# Verify backend started
$backendRunning = Get-Process -Id $backendJob.Id -ErrorAction SilentlyContinue
if ($backendRunning) {
    Write-Host "   ✓ Backend started (PID: $($backendJob.Id))" -ForegroundColor Green
    Write-Host "   ✓ URL: http://localhost:8000" -ForegroundColor Green
    Write-Host "   ✓ Docs: http://localhost:8000/docs" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend failed to start" -ForegroundColor Red
    Write-Host "   Check logs: Get-Content $BACKEND_LOG -Tail 50" -ForegroundColor Red
    exit 1
}

# Test backend endpoint
Start-Sleep -Seconds 2
try {
    $healthCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($healthCheck.StatusCode -eq 200) {
        Write-Host "   ✓ Backend health check passed" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Backend health check failed, but process is running" -ForegroundColor Yellow
}

# ================================================================
# 6. START FRONTEND SERVICE
# ================================================================
Write-Host ""
Write-Host "⚛️  Starting React frontend..." -ForegroundColor Yellow

$FRONTEND_DIR = Join-Path $PROJECT_ROOT "frontend"
Set-Location $FRONTEND_DIR

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "   Installing frontend dependencies..." -ForegroundColor Gray
    npm install
}

$FRONTEND_LOG = Join-Path $LOG_DIR "frontend.log"

# Start frontend in new window with log redirection
$frontendJob = Start-Process -FilePath "npm" `
    -ArgumentList "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000" `
    -RedirectStandardOutput $FRONTEND_LOG `
    -RedirectStandardError $FRONTEND_LOG `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 5

# Verify frontend started
$frontendRunning = Get-Process -Id $frontendJob.Id -ErrorAction SilentlyContinue
if ($frontendRunning) {
    Write-Host "   ✓ Frontend started (PID: $($frontendJob.Id))" -ForegroundColor Green
    Write-Host "   ✓ URL: http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Frontend may have failed to start" -ForegroundColor Yellow
    Write-Host "   Check logs: Get-Content $FRONTEND_LOG -Tail 50" -ForegroundColor Yellow
}

Set-Location $PROJECT_ROOT

# ================================================================
# 7. SUMMARY
# ================================================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Services Started Successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Service URLs:" -ForegroundColor Yellow
Write-Host "   • Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "📝 Logs:" -ForegroundColor Yellow
Write-Host "   • Backend:  Get-Content .logs\backend.log -Tail 50 -Wait" -ForegroundColor White
Write-Host "   • Frontend: Get-Content .logs\frontend.log -Tail 50 -Wait" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Process IDs:" -ForegroundColor Yellow
Write-Host "   • Backend:  $($backendJob.Id)" -ForegroundColor White
Write-Host "   • Frontend: $($frontendJob.Id)" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop services:" -ForegroundColor Yellow
Write-Host "   Stop-Process -Id $($backendJob.Id),$($frontendJob.Id)" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
