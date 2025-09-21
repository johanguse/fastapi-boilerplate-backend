# Monitoring and Metrics Guide

This document explains the comprehensive monitoring and metrics system implemented in the FastAPI boilerplate for performance tracking and debugging.

## 📊 Overview

The monitoring system provides real-time insights into application performance, including:

- Request/response metrics (timing, memory, status codes)
- Per-endpoint performance statistics
- Error tracking and analysis
- Memory usage monitoring
- Custom operation timing

## 🎯 Monitoring Endpoints

### Health Check
```
GET /api/v1/health
```

Basic health check endpoint that returns application status and version.

**Response**:
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### Performance Metrics
```
GET /api/v1/metrics
```

Overall application performance summary.

**Response**:
```json
{
  "uptime_seconds": 3600.5,
  "total_requests": 1250,
  "avg_response_time_ms": 45.2,
  "error_rate": 0.02,
  "slowest_endpoints": [
    ["POST /api/v1/organizations", {"avg_time_ms": 120.5, "count": 50}],
    ["GET /api/v1/projects/export/json", {"avg_time_ms": 95.3, "count": 15}]
  ],
  "error_endpoints": [
    ["GET /api/v1/projects/999", {"error_rate": 0.8, "count": 10}]
  ]
}
```

### Endpoint Statistics
```
GET /api/v1/metrics/endpoints
```

Detailed metrics for all endpoints including response times, error rates, and memory usage.

**Response**:
```json
{
  "endpoint_stats": {
    "GET /api/v1/organizations": {
      "count": 150,
      "avg_time_ms": 25.8,
      "min_time_ms": 12.1,
      "max_time_ms": 89.5,
      "error_rate": 0.01,
      "avg_memory_mb": 2.3
    }
  },
  "slowest_endpoints": [...],
  "error_endpoints": [...]
}
```

### Recent Requests
```
GET /api/v1/metrics/recent?limit=50
```

Recent request details for debugging and analysis.

**Parameters**:
- `limit` (optional): Number of recent requests to return (default: 50)

**Response**:
```json
{
  "recent_requests": [
    {
      "path": "/api/v1/organizations",
      "method": "GET",
      "status_code": 200,
      "duration_ms": 23.5,
      "memory_peak_mb": 2.1,
      "timestamp": 1634567890.123,
      "ip_address": "127.0.0.1"
    }
  ]
}
```

## 🚀 Streaming Export Endpoints

Memory-efficient data export endpoints for large datasets:

### Organization Exports
```
GET /api/v1/organizations/export/json
GET /api/v1/organizations/export/csv
```

### Project Exports  
```
GET /api/v1/projects/export/json
GET /api/v1/projects/export/csv
```

**Benefits**:
- 80-90% memory reduction for large datasets
- Constant memory usage regardless of data size
- Suitable for exports with thousands of records

## 🔧 Implementation Details

### Monitoring Middleware

The performance monitoring is implemented as ASGI middleware for maximum efficiency:

```python
class PerformanceMiddleware:
    def __init__(self, app: ASGIApp, enable_memory_tracking: bool = True):
        self.app = app
        self.enable_memory_tracking = enable_memory_tracking
        
        if self.enable_memory_tracking:
            tracemalloc.start()
```

**Features**:
- Request timing with microsecond precision
- Memory tracking (peak and current usage)
- IP address detection (including X-Forwarded-For)
- User agent logging
- Automatic slow request detection

### Metrics Collection

Metrics are stored in-memory with configurable history limits:

```python
@dataclass
class RequestMetrics:
    path: str
    method: str
    status_code: int
    duration_ms: float
    memory_peak_mb: float
    memory_current_mb: float
    timestamp: float
    user_agent: str
    ip_address: str
```

### Function Timing Decorator

For detailed operation tracking:

```python
@time_operation("database_query")
async def complex_database_operation():
    # Operation is automatically timed
    pass
```

**Usage Examples**:
```python
# Already implemented in services
@time_operation("create_organization")
async def create_organization(db, org, user): ...

@time_operation("get_user_organizations")  
async def get_user_organizations(db, user): ...

@time_operation("invite_to_organization")
async def invite_to_organization(db, org_id, invite, user): ...
```

## 📈 Metrics Analysis

### Performance Thresholds

The system automatically flags performance issues:

- **Slow Requests**: > 1000ms (logged as warnings)
- **Memory Alerts**: Unusual memory spikes
- **Error Tracking**: 4xx and 5xx status codes
- **Operation Timing**: Custom operations > 100ms

### Key Performance Indicators (KPIs)

1. **Response Time Percentiles**
   - P50 (median): Typical user experience
   - P95: Nearly all users
   - P99: Worst-case scenarios

2. **Error Rates**
   - Overall error rate < 1%
   - Per-endpoint error tracking
   - Error pattern analysis

3. **Memory Usage**
   - Peak memory per request
   - Memory growth trends
   - Memory leak detection

4. **Throughput**
   - Requests per second
   - Concurrent request handling
   - Worker utilization

### Dashboard Integration

The metrics can be integrated with monitoring dashboards:

**Prometheus Integration** (example):
```python
# Add to requirements: prometheus-client
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.get("/metrics/prometheus")
async def prometheus_metrics():
    return Response(generate_latest(), media_type="text/plain")
```

**Grafana Dashboard** (example queries):
```promql
# Average response time
rate(request_duration_seconds_sum[5m]) / rate(request_duration_seconds_count[5m])

# Error rate
rate(requests_total{status=~"4..|5.."}[5m]) / rate(requests_total[5m])

# Request throughput
rate(requests_total[5m])
```

## 🛠️ Configuration

### Environment Variables

```bash
# Monitoring configuration
ENABLE_MONITORING=true
MONITORING_MEMORY_TRACKING=true
MONITORING_HISTORY_SIZE=1000

# Alerting thresholds
SLOW_REQUEST_THRESHOLD_MS=1000
HIGH_MEMORY_THRESHOLD_MB=100
```

### Monitoring Setup in Application

```python
# src/main.py
from src.common.monitoring import add_performance_monitoring

# Add monitoring middleware (should be first for accurate timing)
add_performance_monitoring(app)
```

## 🚨 Alerting and Notifications

### Automatic Alerts

The system can be configured to send alerts for:

1. **Performance Degradation**
   - Response times > threshold
   - Error rates > acceptable limits
   - Memory usage spikes

2. **Operational Issues**
   - Application startup failures
   - Database connection issues
   - Critical errors in logs

### Integration Examples

**Slack Notifications**:
```python
async def send_performance_alert(metric: str, value: float, threshold: float):
    if value > threshold:
        await slack_client.post_message(
            f"⚠️ Performance Alert: {metric} = {value} (threshold: {threshold})"
        )
```

**Email Alerts**:
```python
async def check_error_rate():
    current_rate = performance_monitor.get_error_rate()
    if current_rate > 0.05:  # 5% error rate
        await send_email_alert(f"High error rate detected: {current_rate:.2%}")
```

## 📊 Best Practices

### Monitoring Strategy

1. **Monitor What Matters**
   - Focus on user-impacting metrics
   - Track business-critical endpoints
   - Monitor system resource usage

2. **Set Appropriate Thresholds**
   - Base thresholds on historical data
   - Account for normal traffic patterns
   - Adjust for business requirements

3. **Automate Response**
   - Auto-scaling based on metrics
   - Automatic alerting for issues
   - Self-healing mechanisms where possible

### Performance Optimization Workflow

1. **Identify Bottlenecks**
   ```bash
   curl -s http://localhost:8000/api/v1/metrics/endpoints | jq '.slowest_endpoints'
   ```

2. **Analyze Patterns**
   ```bash
   curl -s http://localhost:8000/api/v1/metrics/recent | jq '.recent_requests[] | select(.duration_ms > 100)'
   ```

3. **Implement Fixes**
   - Add caching for expensive operations
   - Optimize database queries
   - Implement streaming for large responses

4. **Verify Improvements**
   - Compare before/after metrics
   - Monitor for regressions
   - Validate under load

## 🔗 Related Documentation

- [Performance Optimization Guide](performance-optimization.md)
- [Production Deployment Guide](production-deployment.md)
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)