#!/bin/bash
# Production startup script for FastAPI Boilerplate Backend
# Optimized for FastAPI performance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
# For multi-tenant API, we use a balanced worker strategy
if command -v uv &> /dev/null; then
    DEFAULT_WORKERS=$(uv run python -c "import os; cpus = os.cpu_count() or 2; print(min(cpus * 2 + 1, 4))")
else
    DEFAULT_WORKERS=$(python -c "import os; cpus = os.cpu_count() or 2; print(min(cpus * 2 + 1, 4))")
fi

DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"

WORKERS=${WORKERS:-$DEFAULT_WORKERS}
HOST=${HOST:-$DEFAULT_HOST}
PORT=${PORT:-$DEFAULT_PORT}
SERVER=${SERVER:-"uvicorn"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

echo -e "${GREEN}🚀 Starting FastAPI Boilerplate Backend${NC}"
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Server: ${SERVER}"
echo -e "  Workers: ${WORKERS}"
echo -e "  Host: ${HOST}"
echo -e "  Port: ${PORT}"
echo -e "  Log Level: ${LOG_LEVEL}"
echo -e "  Environment: ${ENVIRONMENT:-production}"

# Run database migrations
echo -e "${YELLOW}🗃️  Running database migrations...${NC}"
if command -v uv &> /dev/null; then
    uv run alembic upgrade head
else
    alembic upgrade head
fi

# Start Server
echo -e "${GREEN}🚀 Launching application...${NC}"

case $SERVER in
    "gunicorn")
        exec gunicorn src.main:app \
            --workers $WORKERS \
            --worker-class uvicorn.workers.UvicornWorker \
            --bind $HOST:$PORT \
            --log-level $LOG_LEVEL \
            --timeout 120 \
            --keep-alive 5 \
            --preload
        ;;
    "uvicorn")
        exec uvicorn src.main:app \
            --host $HOST \
            --port $PORT \
            --workers $WORKERS \
            --log-level $LOG_LEVEL
        ;;
    "fastapi")
        exec fastapi run src/main.py \
            --workers $WORKERS \
            --host $HOST \
            --port $PORT
        ;;
    *)
        echo -e "${RED}❌ Unknown server: $SERVER${NC}"
        echo "Available options: gunicorn, uvicorn, fastapi"
        exit 1
        ;;
esac