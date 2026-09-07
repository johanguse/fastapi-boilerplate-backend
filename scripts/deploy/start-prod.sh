#!/bin/bash

# Production startup script with optimized settings
# This script provides better defaults for production deployment

# Calculate optimal worker count based on CPU cores
WORKERS=${WORKERS:-$(nproc)}
MAX_WORKERS=${MAX_WORKERS:-8}

# Limit workers to avoid resource exhaustion
if [ "$WORKERS" -gt "$MAX_WORKERS" ]; then
    WORKERS=$MAX_WORKERS
fi

# Ensure at least 1 worker
if [ "$WORKERS" -lt 1 ]; then
    WORKERS=1
fi

echo "Starting FastAPI application with $WORKERS workers"

# Start Gunicorn with optimized settings
exec gunicorn src.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $WORKERS \
    --bind 0.0.0.0:${PORT:-8000} \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keepalive 5 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info