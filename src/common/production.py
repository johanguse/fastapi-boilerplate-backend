"""
Production configuration for FastAPI application.
Optimized for high-performance deployment with proper worker management.
"""
import multiprocessing
from typing import Dict, Any


def get_worker_count() -> int:
    """
    Calculate optimal number of workers based on CPU cores.
    
    For I/O-heavy applications (like most web APIs), you can use more workers 
    than CPU cores. For CPU-heavy applications, use fewer workers.
    
    Returns:
        Recommended number of workers
    """
    cpu_cores = multiprocessing.cpu_count()
    
    # For I/O-heavy applications (recommended for most FastAPI apps)
    # Use 2x CPU cores + 1 (common formula)
    return (cpu_cores * 2) + 1


def get_gunicorn_config() -> Dict[str, Any]:
    """
    Get optimized Gunicorn configuration for production.
    
    Returns:
        Dictionary with Gunicorn configuration options
    """
    worker_count = get_worker_count()
    
    return {
        'bind': '0.0.0.0:8000',
        'workers': worker_count,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'worker_connections': 1000,
        'max_requests': 1000,
        'max_requests_jitter': 50,
        'timeout': 30,
        'keepalive': 2,
        'preload_app': True,
        'access_logfile': '-',
        'error_logfile': '-',
        'log_level': 'info',
        'capture_output': True,
        'enable_stdio_inheritance': True,
    }


def get_uvicorn_config() -> Dict[str, Any]:
    """
    Get optimized Uvicorn configuration for production.
    
    Returns:
        Dictionary with Uvicorn configuration options
    """
    return {
        'host': '0.0.0.0',
        'port': 8000,
        'workers': get_worker_count(),
        'loop': 'uvloop',  # Uses uvloop if available, falls back to asyncio
        'http': 'httptools',  # Uses httptools if available
        'log_level': 'info',
        'access_log': True,
        'use_colors': False,  # Better for production logs
        'server_header': False,  # Don't expose server info
        'date_header': False,  # Small performance gain
    }


# Constants for deployment
PRODUCTION_SETTINGS = {
    'DEBUG': False,
    'RELOAD': False,
    'LOG_LEVEL': 'INFO',
    'SERVER_HEADER': False,
    'DATE_HEADER': False,
}


# Deployment command examples
DEPLOYMENT_COMMANDS = {
    'gunicorn': f'gunicorn src.main:app --workers {get_worker_count()} --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000',
    'uvicorn': f'uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers {get_worker_count()}',
    'fastapi_cli': f'fastapi run src/main.py --workers {get_worker_count()} --host 0.0.0.0 --port 8000',
}


def print_deployment_info():
    """Print deployment configuration information."""
    print(f"🚀 Production Configuration")
    print(f"CPU Cores detected: {multiprocessing.cpu_count()}")
    print(f"Recommended workers: {get_worker_count()}")
    print(f"\n📦 Deployment Commands:")
    for name, command in DEPLOYMENT_COMMANDS.items():
        print(f"{name}: {command}")
    print(f"\n⚙️  Environment Variables to Set:")
    print("DATABASE_URL=postgresql://user:pass@host:5432/dbname")
    print("SECRET_KEY=your-secret-key-here")
    print("JWT_SECRET=your-jwt-secret-here")
    print("FRONTEND_URL=https://yourdomain.com")


if __name__ == "__main__":
    print_deployment_info()