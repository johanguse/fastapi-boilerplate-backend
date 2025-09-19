#!/bin/bash
"""
Production startup script for FastAPI boilerplate.
Handles different deployment scenarios and optimizations.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_WORKERS=$(python -c "import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)")
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"

# Environment variables with defaults
WORKERS=${WORKERS:-$DEFAULT_WORKERS}
HOST=${HOST:-$DEFAULT_HOST}
PORT=${PORT:-$DEFAULT_PORT}
SERVER=${SERVER:-"gunicorn"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

echo -e "${GREEN}🚀 Starting FastAPI Boilerplate${NC}"
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Server: ${SERVER}"
echo -e "  Workers: ${WORKERS}"
echo -e "  Host: ${HOST}"
echo -e "  Port: ${PORT}"
echo -e "  Log Level: ${LOG_LEVEL}"

# Check if performance packages are installed
echo -e "${YELLOW}📦 Checking performance packages...${NC}"

# Check for uvloop
if python -c "import uvloop" 2>/dev/null; then
    echo -e "${GREEN}✓ uvloop found${NC}"
else
    echo -e "${RED}⚠ uvloop not found - install for 2-4x better performance${NC}"
fi

# Check for httptools
if python -c "import httptools" 2>/dev/null; then
    echo -e "${GREEN}✓ httptools found${NC}"
else
    echo -e "${RED}⚠ httptools not found - install for 40% faster HTTP parsing${NC}"
fi

# Check for orjson
if python -c "import orjson" 2>/dev/null; then
    echo -e "${GREEN}✓ orjson found${NC}"
else
    echo -e "${RED}⚠ orjson not found - install for 20-50% faster JSON${NC}"
fi

# Validate required environment variables
echo -e "${YELLOW}🔍 Validating environment...${NC}"

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL not set${NC}"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo -e "${RED}❌ SECRET_KEY not set${NC}"
    exit 1
fi

if [ -z "$JWT_SECRET" ]; then
    echo -e "${RED}❌ JWT_SECRET not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment validation passed${NC}"

# Run database migrations
echo -e "${YELLOW}🗃️  Running database migrations...${NC}"
alembic upgrade head

# Start the server based on SERVER environment variable
echo -e "${GREEN}🚀 Starting server with ${WORKERS} workers...${NC}"

case $SERVER in
    "gunicorn")
        exec gunicorn src.main:app \
            --workers $WORKERS \
            --worker-class uvicorn.workers.UvicornWorker \
            --bind $HOST:$PORT \
            --log-level $LOG_LEVEL \
            --access-logfile - \
            --error-logfile - \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --timeout 30 \
            --keepalive 2 \
            --preload-app
        ;;
    "uvicorn")
        exec uvicorn src.main:app \
            --host $HOST \
            --port $PORT \
            --workers $WORKERS \
            --log-level $LOG_LEVEL \
            --no-server-header \
            --no-date-header
        ;;
    "fastapi")
        exec fastapi run src/main.py \
            --workers $WORKERS \
            --host $HOST \
            --port $PORT \
            --log-level $LOG_LEVEL
        ;;
    *)
        echo -e "${RED}❌ Unknown server: $SERVER${NC}"
        echo -e "Available options: gunicorn, uvicorn, fastapi"
        exit 1
        ;;
esac