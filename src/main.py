import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi_pagination import add_pagination
from slowapi.errors import RateLimitExceeded

from src.auth.admin_routes import router as admin_router
from src.auth.email_routes import router as auth_email_router
from src.auth.routes import router as auth_router
from src.auth.user_routes import router as user_router
from src.ai_analytics.routes import router as ai_analytics_router
from src.ai_content.routes import router as ai_content_router
from src.ai_core.billing_routes import router as ai_billing_router
from src.ai_core.dashboard_routes import router as ai_dashboard_router
from src.ai_core.routes import router as ai_usage_router
from src.ai_documents.routes import router as ai_documents_router
from src.common.config import settings
from src.common.database import Base
from src.common.health import router as health_router
from src.common.middleware import add_i18n_middleware, add_logging_middleware
from src.common.monitoring import add_performance_monitoring
from src.common.openapi import custom_openapi
from src.common.rate_limiter import limiter, rate_limit_exceeded_handler
from src.common.session import engine
from src.organizations.routes import router as org_router
from src.payments.routes import router as payments_router
from src.payments.webhooks import router as payments_webhook_router
from src.projects.routes import router as project_router
from src.subscriptions.routes import router as subscriptions_router
from src.subscriptions.webhooks import router as subscriptions_webhook_router
from src.uploads.routes import router as uploads_router

# Production optimizations
IS_PRODUCTION = os.getenv('ENVIRONMENT', 'development') == 'production'

# Configure logging for production
if IS_PRODUCTION:
    # Structured JSON logging for production
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/app.log'),
        ],
    )
else:
    # Human-readable logging for development
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Update the database URL to use the correct format
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace(
    'postgresql://', 'postgresql+asyncpg://'
)

# Remove this line since we're importing engine from common.database
# engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from src.common.audit_logger import AuditLogger, EventStatus

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info('Database tables created')

    # Log application startup
    AuditLogger.log_system_event(
        action='application_startup',
        status=EventStatus.SUCCESS,
        metadata={
            'environment': 'production' if IS_PRODUCTION else 'development',
            'version': settings.PROJECT_VERSION,
        },
    )

    yield

    # Shutdown
    logger.info('Application shutting down')
    AuditLogger.log_system_event(
        action='application_shutdown',
        status=EventStatus.SUCCESS,
    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    # Hide API docs in production for security
    docs_url='/docs' if not IS_PRODUCTION else None,
    redoc_url='/redoc' if not IS_PRODUCTION else None,
    openapi_url='/openapi.json' if not IS_PRODUCTION else None,
    default_response_class=ORJSONResponse,
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add middleware
add_performance_monitoring(app)  # Add first for accurate timing
add_i18n_middleware(app)
add_logging_middleware(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

add_pagination(app)

# Add routers directly to main app with API prefix
app.include_router(
    health_router,
    prefix=settings.API_V1_STR,
)
app.include_router(
    auth_router,
    prefix='/api/v1',
)
app.include_router(
    auth_email_router,
    prefix='/api/v1',
)
app.include_router(
    user_router,
    prefix=settings.API_V1_STR,
)
app.include_router(
    admin_router,
    prefix=settings.API_V1_STR,
)
# Legacy Teams router removed from public API (replaced by Organizations)
app.include_router(
    org_router,
    prefix=f'{settings.API_V1_STR}/organizations',
    tags=['organizations'],
)
app.include_router(
    project_router, prefix=f'{settings.API_V1_STR}/projects', tags=['projects']
)
app.include_router(
    payments_router,
    prefix=f'{settings.API_V1_STR}/payments',
    tags=['payments'],
)
app.include_router(
    payments_webhook_router,
    prefix=f'{settings.API_V1_STR}/payments',
    tags=['payments'],
)
app.include_router(
    subscriptions_router,
    prefix=f'{settings.API_V1_STR}/subscriptions',
    tags=['subscriptions'],
)
app.include_router(
    subscriptions_webhook_router,
    prefix=f'{settings.API_V1_STR}/webhooks',
    tags=['webhooks'],
)
app.include_router(
    uploads_router, prefix=f'{settings.API_V1_STR}/uploads', tags=['uploads']
)

# AI Features
app.include_router(
    ai_usage_router,
    prefix=f'{settings.API_V1_STR}/ai-usage',
    tags=['AI Usage'],
)
app.include_router(
    ai_billing_router,
    prefix=f'{settings.API_V1_STR}/ai-billing',
    tags=['AI Billing'],
)
app.include_router(
    ai_dashboard_router,
    prefix=f'{settings.API_V1_STR}/ai-dashboard',
    tags=['AI Dashboard'],
)
app.include_router(
    ai_documents_router,
    prefix=f'{settings.API_V1_STR}/ai-documents',
    tags=['AI Documents'],
)
app.include_router(
    ai_content_router,
    prefix=f'{settings.API_V1_STR}/ai-content',
    tags=['AI Content'],
)
app.include_router(
    ai_analytics_router,
    prefix=f'{settings.API_V1_STR}/ai-analytics',
    tags=['AI Analytics'],
)

# Custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)
