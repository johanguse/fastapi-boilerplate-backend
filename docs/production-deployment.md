# Production Deployment Guide

This guide covers optimized deployment configurations for high-performance FastAPI applications.

## 🚀 Quick Start

### Option 1: Gunicorn (Recommended)

```bash
# Install dependencies
uv sync --no-dev

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
chmod +x scripts/deploy/start-production.sh
./scripts/deploy/start-production.sh
```

## 🚀 Deployment to Fly.io

### Deployment Commands

```bash
# Deploy to staging (code only - faster)
./scripts/deploy/deploy-staging.sh

# Deploy to staging and update environment variables
./scripts/deploy/deploy-staging.sh --set-vars

# Deploy to production (code only - faster)
./scripts/deploy/deploy-production.sh

# Deploy to production and update environment variables
./scripts/deploy/deploy-production.sh --set-vars
```

### Understanding `--set-vars` Flag

The `--set-vars` flag controls whether environment variables are updated during deployment:

**Without `--set-vars` (default)**:
- ✅ Faster deployments
- ✅ Skips environment variable updates
- ✅ Ideal for code-only changes
- ✅ Won't accidentally overwrite secrets
- ⏱️ Typical deployment: 2-3 minutes

**With `--set-vars`**:
- 📋 Loads variables from `.env.staging` or `.env.production`
- 🔄 Updates all secrets on Fly.io
- ⚠️  Required for first deployment
- ⚠️  Use when secrets have changed
- ⏱️ Typical deployment: 5-8 minutes

**When to use `--set-vars`**:
1. **First deployment** - Initial setup requires all secrets
2. **Updated secrets** - Changed API keys, database credentials, etc.
3. **New variables** - Added new environment variables to your app
4. **Troubleshooting** - Environment variable issues

**When to skip `--set-vars`**:
1. **Code changes only** - Just updated application code
2. **Regular deployments** - Daily/weekly code updates
3. **Quick hotfixes** - Bug fixes that don't need config changes

## 🚂 Deployment to Railway

Railway is supported as an alternative to Fly.io via [`railway.toml`](../railway.toml), [`nixpacks.toml`](../nixpacks.toml), and [`Dockerfile.railway`](../Dockerfile.railway).

### Option A: Nixpacks (default)

Railway auto-detects `railway.toml` and builds with Nixpacks using `nixpacks.toml`, which installs dependencies with `uv sync --frozen --no-dev` and starts the app via `scripts/deploy/start-production.sh`.

1. Create a new Railway project and connect this repository
2. Railway picks up `railway.toml` automatically — no extra configuration needed
3. Add a Postgres plugin (or point `DATABASE_URL` at an external database)

### Option B: Custom Dockerfile

If Nixpacks builds fail (e.g. native dependency compilation issues), switch the service's builder to "Dockerfile" in the Railway dashboard and set the Dockerfile path to `Dockerfile.railway`. This multi-stage build compiles native dependencies (`asyncpg`, etc.) in a builder stage and ships a slim, non-root runtime image.

### Environment Variables (Railway)

Set these in the Railway dashboard (Variables tab):

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### Health Check

Both `railway.toml` and `Dockerfile.railway` point at `/api/v1/health` — Railway uses this to determine when a deployment is healthy.

### Post-Deployment

Run migrations from the Railway shell (or a one-off command):

```bash
railway run uv run alembic upgrade head
```

## ⚡ Performance Optimizations

### Installed Optimizations

- ✅ **ORJSON**: 20-50% faster JSON serialization
- ✅ **GZip Compression**: 80-90% bandwidth reduction for large responses
- ✅ **Async Middleware**: 40% faster than BaseHTTPMiddleware

### Additional Optimizations (Install if needed)

```bash
# For Linux/macOS (Windows not supported)
uv add uvloop httptools

# All platforms
uv add orjson  # Already installed
```

### Performance Features

- 🔄 **Dependency Caching**: `@lru_cache` on expensive operations
- 📡 **Streaming Responses**: Memory-efficient large data exports
- 🏗️ **Multi-worker**: Utilizes all CPU cores
- 📊 **Database Streaming**: Batch processing for large queries

## 🐳 Docker Deployment

### Dockerfile Optimization

```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

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
CMD ["./scripts/deploy/start-production.sh"]
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
