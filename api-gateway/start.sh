#!/bin/bash
# Start script for API Gateway
# Uses PORT environment variable from Railway, defaults to 8001

PORT=${PORT:-8001}
echo "Starting API Gateway on port $PORT"
exec uvicorn src.main:app --host 0.0.0.0 --port "$PORT"
