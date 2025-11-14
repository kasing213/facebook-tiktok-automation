#!/usr/bin/env bash
# ================================================================
# Kill processes on ports 8000 and 3000
# Usage: bash scripts/kill_ports.sh
# ================================================================

set -e

echo "🛑 Killing processes on ports 8000 and 3000..."
echo ""

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    echo "Checking port $port..."

    # Method 1: lsof
    if command -v lsof &> /dev/null; then
        PIDS=$(sudo lsof -ti:$port 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            echo "  Found PIDs: $PIDS"
            echo "$PIDS" | xargs -r sudo kill -9
            echo "  ✓ Killed processes on port $port"
        else
            echo "  ℹ️  No process found on port $port (lsof)"
        fi
    fi

    # Method 2: netstat (backup)
    if command -v netstat &> /dev/null; then
        PIDS=$(sudo netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -E '^[0-9]+$' || true)
        if [ -n "$PIDS" ]; then
            echo "  Found PIDs via netstat: $PIDS"
            echo "$PIDS" | xargs -r sudo kill -9
            echo "  ✓ Killed processes on port $port (netstat)"
        fi
    fi

    # Method 3: fuser (if available)
    if command -v fuser &> /dev/null; then
        sudo fuser -k $port/tcp 2>/dev/null || true
        echo "  ✓ Attempted fuser kill on port $port"
    fi
}

# Kill port 8000 (backend)
kill_port 8000

echo ""

# Kill port 3000 (frontend)
kill_port 3000

echo ""

# Also kill by process name
echo "Killing by process name..."
pkill -9 -f "uvicorn" 2>/dev/null || echo "  ℹ️  No uvicorn processes"
pkill -9 -f "vite" 2>/dev/null || echo "  ℹ️  No vite processes"

echo ""
echo "✅ Done! Ports should be free now."
echo ""
echo "Verify with:"
echo "  sudo lsof -i :8000"
echo "  sudo lsof -i :3000"
