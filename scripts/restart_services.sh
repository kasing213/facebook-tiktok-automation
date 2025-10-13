#!/usr/bin/env bash
# ================================================================
# Facebook/TikTok Automation - Unified Service Startup Script
# ================================================================
# This script starts both backend (FastAPI) and frontend (React)
# Usage: bash scripts/restart_services.sh
# ================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "Facebook/TikTok Automation Startup"
echo "=========================================="
echo ""

# ================================================================
# 1. STOP EXISTING SERVICES
# ================================================================
echo "🛑 Stopping existing services..."

# Kill processes on port 8000 (backend)
if command -v lsof &> /dev/null; then
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
elif command -v netstat &> /dev/null; then
    # Windows/Git Bash fallback
    netstat -ano | grep ":8000" | awk '{print $5}' | xargs -r taskkill //F //PID 2>/dev/null || true
fi

# Kill processes on port 3000 (frontend)
if command -v lsof &> /dev/null; then
    lsof -ti:3000 | xargs -r kill -9 2>/dev/null || true
elif command -v netstat &> /dev/null; then
    netstat -ano | grep ":3000" | awk '{print $5}' | xargs -r taskkill //F //PID 2>/dev/null || true
fi

# Kill by process pattern as backup
pkill -9 -f "uvicorn app.main" 2>/dev/null || true
pkill -9 -f "python -m app.bot" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
pkill -9 -f "npm.*dev" 2>/dev/null || true

echo "   ✓ Stopped existing processes"
sleep 2

# ================================================================
# 2. SETUP PYTHON ENVIRONMENT
# ================================================================
echo ""
echo "🐍 Setting up Python environment..."

# Create venv if it doesn't exist
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv "${PROJECT_ROOT}/.venv" || python -m venv "${PROJECT_ROOT}/.venv"
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows/Git Bash
    source "${PROJECT_ROOT}/.venv/Scripts/activate"
else
    # Linux/macOS
    source "${PROJECT_ROOT}/.venv/bin/activate"
fi

echo "   ✓ Virtual environment activated"

# Install/update dependencies if needed
if [ ! -f "${PROJECT_ROOT}/.venv/.dependencies_installed" ]; then
    echo "   Installing Python dependencies..."
    pip install -q uvicorn fastapi sqlalchemy alembic psycopg2-binary python-dotenv cryptography httpx pydantic-settings redis python-multipart
    touch "${PROJECT_ROOT}/.venv/.dependencies_installed"
    echo "   ✓ Dependencies installed"
else
    echo "   ✓ Dependencies already installed"
fi

# Always ensure python-multipart is installed (required for Form data)
pip show python-multipart > /dev/null 2>&1 || pip install -q python-multipart

# ================================================================
# 3. CREATE LOG DIRECTORY
# ================================================================
mkdir -p "${PROJECT_ROOT}/.logs"

# ================================================================
# 4. CHECK DATABASE CONNECTION
# ================================================================
echo ""
echo "🗄️  Checking database connection..."
if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 -U fbauto &> /dev/null; then
        echo "   ✓ PostgreSQL is running"
    else
        echo "   ⚠️  PostgreSQL may not be running on localhost:5432"
        echo "   Backend may fail to start if database is not available"
    fi
else
    echo "   ℹ️  pg_isready not found, skipping database check"
fi

# ================================================================
# 5. START BACKEND SERVICE
# ================================================================
echo ""
echo "🚀 Starting FastAPI backend..."

cd "${PROJECT_ROOT}"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "${PROJECT_ROOT}/.logs/backend.log" 2>&1 &
BACKEND_PID=$!

sleep 3

# Verify backend started
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "   ✓ Backend started (PID: $BACKEND_PID)"
    echo "   ✓ URL: http://localhost:8000"
    echo "   ✓ Docs: http://localhost:8000/docs"
else
    echo "   ❌ Backend failed to start"
    echo "   Check logs: tail -f .logs/backend.log"
    exit 1
fi

# ================================================================
# 6. START FRONTEND SERVICE
# ================================================================
echo ""
echo "⚛️  Starting React frontend..."

cd "${PROJECT_ROOT}/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   Installing frontend dependencies..."
    npm install
fi

nohup npm run dev -- --host 0.0.0.0 --port 3000 > "${PROJECT_ROOT}/.logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

sleep 3

# Verify frontend started
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "   ✓ Frontend started (PID: $FRONTEND_PID)"
    echo "   ✓ URL: http://localhost:3000"
else
    echo "   ⚠️  Frontend may have failed to start"
    echo "   Check logs: tail -f .logs/frontend.log"
fi

cd "${PROJECT_ROOT}"

# ================================================================
# 7. SUMMARY
# ================================================================
echo ""
echo "=========================================="
echo "✅ Services Started Successfully!"
echo "=========================================="
echo ""
echo "📊 Service URLs:"
echo "   • Backend:  http://localhost:8000"
echo "   • Frontend: http://localhost:3000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • Backend:  tail -f .logs/backend.log"
echo "   • Frontend: tail -f .logs/frontend.log"
echo ""
echo "🔧 Process IDs:"
echo "   • Backend:  $BACKEND_PID"
echo "   • Frontend: $FRONTEND_PID"
echo ""
echo "🛑 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=========================================="
