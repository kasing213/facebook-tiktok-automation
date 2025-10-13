#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/.logs"

if [[ ! -d "${PROJECT_ROOT}/.venv" ]]; then
  echo "Virtual environment not found at ${PROJECT_ROOT}/.venv" >&2
  exit 1
fi

mkdir -p "${LOG_DIR}"

source "${PROJECT_ROOT}/.venv/bin/activate"

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . <(tr -d '\r' < "${PROJECT_ROOT}/.env")
  set +a
else
  echo ".env file not found in project root" >&2
  exit 1
fi

ensure_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command '$1' is not available in PATH" >&2
    exit 1
  fi
}

ensure_command uvicorn
ensure_command python

if command -v docker >/dev/null 2>&1; then
  if docker ps --format '{{.Names}}' | grep -qx 'postgres-local'; then
    :
  elif docker ps -a --format '{{.Names}}' | grep -qx 'postgres-local'; then
    echo "Starting Docker container postgres-local..."
    docker start postgres-local >/dev/null
  fi
fi

start_process() {
  local pattern="$1"
  shift
  local log_file="$1"
  shift

  if pgrep -f "${pattern}" >/dev/null 2>&1; then
    echo "Process matching '${pattern}' already running"
  else
    echo "Starting ${pattern}..."
    nohup "$@" >"${log_file}" 2>&1 &
  fi
}

API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

start_process "uvicorn app.main:app" "${LOG_DIR}/backend.log" \
  uvicorn app.main:app --host 0.0.0.0 --port "${API_PORT}" --reload

start_process "python -m app.bot" "${LOG_DIR}/bot.log" \
  python -m app.bot

if [[ -d "${PROJECT_ROOT}/frontend" ]]; then
  ensure_command npm
  pushd "${PROJECT_ROOT}/frontend" >/dev/null
  start_process "npm run dev -- --host" "${LOG_DIR}/frontend.log" \
    npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}"
  popd >/dev/null
fi

echo "Services started. Logs available in ${LOG_DIR}."
