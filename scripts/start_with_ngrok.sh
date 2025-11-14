#!/usr/bin/env bash
# Start backend with ngrok for Facebook App Review

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================="
echo "Starting Backend with ngrok"
echo "=========================================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo ""
    echo "Please install ngrok:"
    echo "  1. Download from: https://ngrok.com/download"
    echo "  2. Or install via: choco install ngrok"
    echo ""
    exit 1
fi

echo "✓ ngrok is installed"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend is not running on port 8000"
    echo ""
    echo "Please start the backend first:"
    echo "  bash scripts/restart_services.sh"
    echo ""
    exit 1
fi

echo "✓ Backend is running on port 8000"
echo ""

# Start ngrok
echo "🚀 Starting ngrok tunnel..."
echo ""
echo "This will expose your local backend to the internet."
echo "Press Ctrl+C to stop."
echo ""
echo "=========================================="

# Start ngrok (this will block)
ngrok http 8000 --log=stdout
