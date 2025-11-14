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
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows/Git Bash - use taskkill
    for pid in $(netstat -ano | grep ":8000" | grep "LISTENING" | awk '{print $5}' | sort -u); do
        taskkill //F //PID $pid 2>/dev/null || true
    done
else
    # Linux/macOS
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
    pkill -9 -f "uvicorn app.main" 2>/dev/null || true
fi

# Kill processes on port 3000 (frontend)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows/Git Bash - use taskkill
    for pid in $(netstat -ano | grep ":3000" | grep "LISTENING" | awk '{print $5}' | sort -u); do
        taskkill //F //PID $pid 2>/dev/null || true
    done
else
    # Linux/macOS
    lsof -ti:3000 | xargs -r kill -9 2>/dev/null || true
    pkill -9 -f "vite" 2>/dev/null || true
    pkill -9 -f "npm.*dev" 2>/dev/null || true
fi

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
    if [ -f "${PROJECT_ROOT}/.venv/Scripts/activate" ]; then
        source "${PROJECT_ROOT}/.venv/Scripts/activate"
        echo "   ✓ Virtual environment activated (Windows)"
    elif [ -f "${PROJECT_ROOT}/.venv/bin/activate" ]; then
        # WSL venv detected, recreate for Windows
        echo "   ⚠️  WSL venv detected, recreating for Windows..."
        rm -rf "${PROJECT_ROOT}/.venv"
        python -m venv "${PROJECT_ROOT}/.venv"
        source "${PROJECT_ROOT}/.venv/Scripts/activate"
        rm -f "${PROJECT_ROOT}/.venv/.dependencies_installed"
        echo "   ✓ Virtual environment recreated for Windows"
    else
        echo "   ❌ Failed to find activation script"
        exit 1
    fi
else
    # Linux/macOS/WSL
    if [ -f "${PROJECT_ROOT}/.venv/bin/activate" ]; then
        source "${PROJECT_ROOT}/.venv/bin/activate"
        echo "   ✓ Virtual environment activated (Linux/WSL)"
    elif [ -d "${PROJECT_ROOT}/.venv/Scripts" ] || [ -f "${PROJECT_ROOT}/.venv/Scripts/activate" ]; then
        # Windows venv detected (Scripts dir exists), recreate for Linux/WSL
        echo "   ⚠️  Windows venv detected, recreating for Linux/WSL..."
        # Try to remove, if fails, rename and create new
        if ! rm -rf "${PROJECT_ROOT}/.venv" 2>/dev/null; then
            echo "   ℹ️  Cannot remove .venv (file locks), renaming to .venv.old"
            mv "${PROJECT_ROOT}/.venv" "${PROJECT_ROOT}/.venv.old" 2>/dev/null || true
        fi
        python3 -m venv "${PROJECT_ROOT}/.venv" || python -m venv "${PROJECT_ROOT}/.venv"
        source "${PROJECT_ROOT}/.venv/bin/activate"
        rm -f "${PROJECT_ROOT}/.venv/.dependencies_installed"
        echo "   ✓ Virtual environment recreated for Linux/WSL"
    elif [ -d "${PROJECT_ROOT}/.venv" ]; then
        # .venv exists but corrupted, recreate
        echo "   ⚠️  Corrupted venv detected, recreating..."
        if ! rm -rf "${PROJECT_ROOT}/.venv" 2>/dev/null; then
            echo "   ℹ️  Cannot remove .venv (file locks), renaming to .venv.old"
            mv "${PROJECT_ROOT}/.venv" "${PROJECT_ROOT}/.venv.old" 2>/dev/null || true
        fi
        python3 -m venv "${PROJECT_ROOT}/.venv" || python -m venv "${PROJECT_ROOT}/.venv"
        source "${PROJECT_ROOT}/.venv/bin/activate"
        echo "   ✓ Virtual environment recreated"
    else
        # No venv exists, create new one
        echo "   Creating new virtual environment for WSL..."
        python3 -m venv "${PROJECT_ROOT}/.venv" || python -m venv "${PROJECT_ROOT}/.venv"
        source "${PROJECT_ROOT}/.venv/bin/activate"
        echo "   ✓ Virtual environment created"
    fi
fi

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
# 4. CHECK DATABASE CONNECTION & FIX WSL NETWORKING
# ================================================================
echo ""
echo "🗄️  Checking database connection..."

# On Windows, check if PostgreSQL is in WSL and update DATABASE_URL accordingly
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    if command -v wsl &> /dev/null; then
        # Get WSL IP address
        WSL_IP=$(wsl -- hostname -I 2>/dev/null | awk '{print $1}')
        if [ -n "$WSL_IP" ]; then
            echo "   ℹ️  Detected WSL PostgreSQL at $WSL_IP"

            # Update DATABASE_URL to use WSL IP instead of localhost
            if [ -f "${PROJECT_ROOT}/.env" ]; then
                # Check if DATABASE_URL uses localhost
                if grep -q "DATABASE_URL=postgresql.*://.*@localhost:" "${PROJECT_ROOT}/.env"; then
                    echo "   🔧 Updating DATABASE_URL to use WSL IP..."
                    # Create backup
                    cp "${PROJECT_ROOT}/.env" "${PROJECT_ROOT}/.env.bak"
                    # Replace localhost with WSL IP
                    sed -i "s|@localhost:|@${WSL_IP}:|g" "${PROJECT_ROOT}/.env"
                    echo "   ✓ DATABASE_URL updated to use $WSL_IP"
                    echo "   ℹ️  Backup saved to .env.bak"
                fi
            fi
        fi
    fi
else
    # Running in WSL/Linux - restore localhost if DATABASE_URL uses IP
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        if grep -q "DATABASE_URL=postgresql.*://.*@172\.22\." "${PROJECT_ROOT}/.env"; then
            echo "   ℹ️  Running in WSL, restoring localhost in DATABASE_URL..."
            # Create backup
            cp "${PROJECT_ROOT}/.env" "${PROJECT_ROOT}/.env.bak"
            # Replace WSL IP with localhost
            sed -i "s|@172\.22\.[0-9]\+\.[0-9]\+:|@localhost:|g" "${PROJECT_ROOT}/.env"
            echo "   ✓ DATABASE_URL restored to use localhost"
        fi
    fi
fi

if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 -U fbauto &> /dev/null; then
        echo "   ✓ PostgreSQL is running on localhost"
    else
        echo "   ⚠️  PostgreSQL may not be running on localhost:5432"
    fi
else
    echo "   ℹ️  pg_isready not found, skipping connection check"
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
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows: Check if port is listening
    sleep 2
    if netstat -ano | grep ":8000" | grep "LISTENING" > /dev/null; then
        echo "   ✓ Backend started (PID: $BACKEND_PID)"
        echo "   ✓ URL: http://localhost:8000"
        echo "   ✓ Docs: http://localhost:8000/docs"
    else
        echo "   ❌ Backend failed to start"
        echo "   Check logs: tail -f .logs/backend.log"
        exit 1
    fi
else
    # Linux/macOS: Check process
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "   ✓ Backend started (PID: $BACKEND_PID)"
        echo "   ✓ URL: http://localhost:8000"
        echo "   ✓ Docs: http://localhost:8000/docs"
    else
        echo "   ❌ Backend failed to start"
        echo "   Check logs: tail -f .logs/backend.log"
        exit 1
    fi
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
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows: Check if port is listening
    sleep 2
    if netstat -ano | grep ":3000" | grep "LISTENING" > /dev/null; then
        echo "   ✓ Frontend started (PID: $FRONTEND_PID)"
        echo "   ✓ URL: http://localhost:3000"
    else
        echo "   ⚠️  Frontend may have failed to start"
        echo "   Check logs: tail -f .logs/frontend.log"
    fi
else
    # Linux/macOS: Check process
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "   ✓ Frontend started (PID: $FRONTEND_PID)"
        echo "   ✓ URL: http://localhost:3000"
    else
        echo "   ⚠️  Frontend may have failed to start"
        echo "   Check logs: tail -f .logs/frontend.log"
    fi
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
