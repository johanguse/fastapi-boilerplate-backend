from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.common.config import settings
from src.common.monitoring import PerformanceMonitor, get_performance_monitor


class HealthResponse(BaseModel):
    status: str = 'ok'
    version: str


class PerformanceMetrics(BaseModel):
    uptime_seconds: float
    total_requests: int
    avg_response_time_ms: float
    error_rate: float
    slowest_endpoints: list
    error_endpoints: list


router = APIRouter(tags=['Health'])


@router.get('/health', response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and Docker healthcheck
    """
    return HealthResponse(
        status='ok',
        version=settings.PROJECT_VERSION,
    )


@router.get('/metrics', response_model=PerformanceMetrics)
async def get_performance_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get performance metrics and statistics.
    Useful for monitoring application performance and identifying bottlenecks.
    """
    summary = monitor.get_summary()
    return PerformanceMetrics(**summary)


@router.get('/metrics/endpoints')
async def get_endpoint_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get detailed metrics for all endpoints.
    Shows response times, error rates, and memory usage per endpoint.
    """
    return {
        'endpoint_stats': monitor.get_endpoint_stats(),
        'slowest_endpoints': monitor.get_slowest_endpoints(10),
        'error_endpoints': monitor.get_error_endpoints(10),
    }


@router.get('/metrics/recent')
async def get_recent_requests(
    limit: int = 50,
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get recent request metrics for debugging.
    Shows last N requests with timing and memory information.
    """
    recent = monitor.get_recent_requests(limit)
    return {
        'recent_requests': [
            {
                'path': req.path,
                'method': req.method,
                'status_code': req.status_code,
                'duration_ms': req.duration_ms,
                'memory_peak_mb': req.memory_peak_mb,
                'timestamp': req.timestamp,
                'ip_address': req.ip_address,
            }
            for req in recent
        ]
    }
