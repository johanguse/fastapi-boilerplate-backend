# Production Deployment Guide

This guide covers optimized deployment configurations for high-performance FastAPI applications.

## 🚀 Quick Start

### Option 1: Gunicorn (Recommended)
```bash
# Install dependencies
poetry install --only=main

# Set environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export SECRET_KEY="your-secret-key-here"
export JWT_SECRET="your-jwt-secret-here"
export ENVIRONMENT="production"

# Start with Gunicorn
gunicorn -c gunicorn.conf.py src.main:app
```

### Option 2: FastAPI CLI
```bash
fastapi run src/main.py --workers 4 --host 0.0.0.0 --port 8000
```

### Option 3: Production Script
```bash
chmod +x scripts/start-production.sh
./scripts/start-production.sh
```

## ⚡ Performance Optimizations

### Installed Optimizations
- ✅ **ORJSON**: 20-50% faster JSON serialization
- ✅ **GZip Compression**: 80-90% bandwidth reduction for large responses
- ✅ **Async Middleware**: 40% faster than BaseHTTPMiddleware

### Additional Optimizations (Install if needed)
```bash
# For Linux/macOS (Windows not supported)
poetry add uvloop httptools

# All platforms
poetry add orjson  # Already installed
```

### Performance Features
- 🔄 **Dependency Caching**: `@lru_cache` on expensive operations
- 📡 **Streaming Responses**: Memory-efficient large data exports
- 🏗️ **Multi-worker**: Utilizes all CPU cores
- 📊 **Database Streaming**: Batch processing for large queries

## 🐳 Docker Deployment

### Dockerfile Optimization
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main

# Copy application
COPY . .

# Production optimizations
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start application
CMD ["./scripts/start-production.sh"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dbname
      - SECRET_KEY=your-secret-key
      - JWT_SECRET=your-jwt-secret
      - ENVIRONMENT=production
      - WORKERS=4
    depends_on:
      - db
    restart: unless-stopped
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=dbname
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WORKERS` | Number of worker processes | CPU cores * 2 + 1 |
| `HOST` | Bind host | 0.0.0.0 |
| `PORT` | Bind port | 8000 |
| `SERVER` | Server type (gunicorn/uvicorn/fastapi) | gunicorn |
| `ENVIRONMENT` | Environment (production/development) | development |
| `LOG_LEVEL` | Log level | info |

### Worker Configuration

The application automatically calculates optimal workers based on your CPU:
- **I/O-heavy workloads** (most APIs): `CPU cores × 2 + 1`
- **CPU-heavy workloads**: `CPU cores`
- **Mixed workloads**: `CPU cores × 1.5`

Override with: `WORKERS=8`

## 📈 Performance Monitoring

### Built-in Endpoints
- `GET /api/v1/health` - Health check with response time
- `GET /api/v1/metrics` - Overall performance metrics
- `GET /api/v1/metrics/endpoints` - Per-endpoint statistics  
- `GET /api/v1/metrics/recent` - Recent request details
- `GET /api/v1/organizations/export/json` - Streaming JSON export
- `GET /api/v1/organizations/export/csv` - Streaming CSV export
- `GET /api/v1/projects/export/json` - Streaming project export
- `GET /api/v1/projects/export/csv` - Streaming project CSV

### Metrics to Monitor
- Response times (via logging middleware)
- Memory usage per worker
- Database connection pool usage
- Queue sizes for background tasks

## 🚦 Load Balancing

### Nginx Configuration
```nginx
upstream fastapi_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔒 Security

### Production Security Checklist
- [ ] Use HTTPS in production
- [ ] Set strong SECRET_KEY and JWT_SECRET
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable request rate limiting
- [ ] Set up proper logging and monitoring
- [ ] Regular security updates

### Rate Limiting
```python
# Add to your requirements if needed
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@limiter.limit("10/minute")
@app.get("/api/v1/limited-endpoint")
async def limited_endpoint(request: Request):
    return {"message": "This endpoint is rate limited"}
```

## 📊 Expected Performance

With all optimizations:
- **20-50% faster JSON responses** (ORJSON)
- **2-4x better throughput** under high concurrency (uvloop)
- **40% faster HTTP parsing** (httptools)
- **80-90% bandwidth reduction** (GZip)
- **40% faster middleware** (ASGI pure)
- **Significant memory reduction** (streaming responses)

## 🐛 Troubleshooting

### Common Issues
1. **High memory usage**: Enable streaming for large responses
2. **Slow startup**: Check database connection and migrations
3. **Poor performance**: Verify uvloop and httptools are installed
4. **Worker crashes**: Increase memory limits or reduce max_requests

### Debug Commands
```bash
# Check if performance packages are installed
python -c "import uvloop; print('uvloop OK')"
python -c "import httptools; print('httptools OK')"
python -c "import orjson; print('orjson OK')"

# Test worker configuration
python src/common/production.py

# Monitor performance
docker stats  # If using Docker
htop  # System monitoring
```