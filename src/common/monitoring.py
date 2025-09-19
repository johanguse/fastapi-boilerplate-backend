"""
Advanced performance monitoring middleware for FastAPI.
Tracks request times, memory usage, database queries, and performance bottlenecks.
"""
import asyncio
import logging
import time
import tracemalloc
from typing import Callable, Dict, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from contextlib import asynccontextmanager

from fastapi import Request, Response
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Container for request performance metrics."""
    path: str
    method: str
    status_code: int
    duration_ms: float
    memory_peak_mb: float
    memory_current_mb: float
    timestamp: float
    user_agent: str
    ip_address: str


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.request_history: deque = deque(maxlen=max_history)
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'error_count': 0,
            'avg_memory': 0.0,
        })
        self.start_time = time.time()
        
    def add_request(self, metrics: RequestMetrics):
        """Add request metrics to history and update statistics."""
        self.request_history.append(metrics)
        
        endpoint_key = f"{metrics.method} {metrics.path}"
        stats = self.endpoint_stats[endpoint_key]
        
        stats['count'] += 1
        stats['total_time'] += metrics.duration_ms
        stats['min_time'] = min(stats['min_time'], metrics.duration_ms)
        stats['max_time'] = max(stats['max_time'], metrics.duration_ms)
        stats['avg_memory'] = (stats['avg_memory'] * (stats['count'] - 1) + metrics.memory_peak_mb) / stats['count']
        
        if metrics.status_code >= 400:
            stats['error_count'] += 1
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get aggregated endpoint statistics."""
        stats = {}
        for endpoint, data in self.endpoint_stats.items():
            if data['count'] > 0:
                stats[endpoint] = {
                    'count': data['count'],
                    'avg_time_ms': data['total_time'] / data['count'],
                    'min_time_ms': data['min_time'],
                    'max_time_ms': data['max_time'],
                    'error_rate': data['error_count'] / data['count'],
                    'avg_memory_mb': data['avg_memory'],
                }
        return stats
    
    def get_recent_requests(self, limit: int = 100) -> list:
        """Get recent request metrics."""
        return list(self.request_history)[-limit:]
    
    def get_slowest_endpoints(self, limit: int = 10) -> list:
        """Get slowest endpoints by average response time."""
        stats = self.get_endpoint_stats()
        sorted_endpoints = sorted(
            stats.items(),
            key=lambda x: x[1]['avg_time_ms'],
            reverse=True
        )
        return sorted_endpoints[:limit]
    
    def get_error_endpoints(self, limit: int = 10) -> list:
        """Get endpoints with highest error rates."""
        stats = self.get_endpoint_stats()
        sorted_endpoints = sorted(
            stats.items(),
            key=lambda x: x[1]['error_rate'],
            reverse=True
        )
        return [(endpoint, data) for endpoint, data in sorted_endpoints[:limit] if data['error_rate'] > 0]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.request_history:
            return {"message": "No requests recorded yet"}
        
        total_requests = len(self.request_history)
        avg_response_time = sum(r.duration_ms for r in self.request_history) / total_requests
        error_count = sum(1 for r in self.request_history if r.status_code >= 400)
        
        return {
            'uptime_seconds': time.time() - self.start_time,
            'total_requests': total_requests,
            'avg_response_time_ms': avg_response_time,
            'error_rate': error_count / total_requests if total_requests > 0 else 0,
            'slowest_endpoints': self.get_slowest_endpoints(5),
            'error_endpoints': self.get_error_endpoints(5),
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


class PerformanceMiddleware:
    """ASGI middleware for performance monitoring."""
    
    def __init__(self, app: ASGIApp, enable_memory_tracking: bool = True):
        self.app = app
        self.enable_memory_tracking = enable_memory_tracking
        
        if self.enable_memory_tracking:
            tracemalloc.start()
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        memory_before = 0
        memory_peak = 0
        
        if self.enable_memory_tracking:
            memory_before = tracemalloc.get_traced_memory()[0] / 1024 / 1024  # MB
        
        # Extract request info
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        headers = dict(scope.get("headers", []))
        user_agent = headers.get(b"user-agent", b"").decode()
        
        # Extract IP address
        ip_address = "unknown"
        if "client" in scope and scope["client"]:
            ip_address = scope["client"][0]
        # Check for forwarded IP
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.decode().split(",")[0].strip()
        
        status_code = 500  # Default to error in case of exception
        
        async def send_with_monitoring(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_with_monitoring)
        except Exception as e:
            logger.error(f"Error in request {method} {path}: {e}")
            status_code = 500
            raise
        finally:
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            
            memory_current = 0
            if self.enable_memory_tracking:
                current, peak = tracemalloc.get_traced_memory()
                memory_current = current / 1024 / 1024  # MB
                memory_peak = peak / 1024 / 1024  # MB
            
            # Create metrics record
            metrics = RequestMetrics(
                path=path,
                method=method,
                status_code=status_code,
                duration_ms=duration_ms,
                memory_peak_mb=memory_peak,
                memory_current_mb=memory_current,
                timestamp=time.time(),
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Add to monitor
            performance_monitor.add_request(metrics)
            
            # Log slow requests
            if duration_ms > 1000:  # Log requests slower than 1 second
                logger.warning(
                    f"Slow request: {method} {path} took {duration_ms:.2f}ms "
                    f"(status: {status_code}, memory peak: {memory_peak:.2f}MB)"
                )
            
            # Log errors
            if status_code >= 400:
                logger.error(
                    f"Error request: {method} {path} returned {status_code} "
                    f"in {duration_ms:.2f}ms"
                )


def add_performance_monitoring(app):
    """Add performance monitoring middleware to FastAPI application."""
    app.add_middleware(PerformanceMiddleware)


# Dependency for accessing performance metrics
def get_performance_monitor() -> PerformanceMonitor:
    """Dependency to get the performance monitor instance."""
    return performance_monitor


class AsyncRequestTimer:
    """Context manager for timing async operations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        
    async def __aenter__(self):
        self.start_time = time.time()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000
        if duration > 100:  # Log operations slower than 100ms
            logger.info(f"Operation '{self.operation_name}' took {duration:.2f}ms")


# Decorator for timing functions
def time_operation(operation_name: str):
    """Decorator to time function execution."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                async with AsyncRequestTimer(operation_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = (time.time() - start_time) * 1000
                    if duration > 100:
                        logger.info(f"Operation '{operation_name}' took {duration:.2f}ms")
            return sync_wrapper
    return decorator