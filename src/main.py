import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi_pagination import add_pagination

from src.auth.email_routes import router as auth_email_router
from src.auth.routes import router as auth_router
from src.auth.user_routes import router as user_router
from src.common.config import settings
from src.common.database import Base
from src.common.health import router as health_router
from src.common.middleware import add_i18n_middleware, add_logging_middleware
from src.common.monitoring import add_performance_monitoring
from src.common.openapi import custom_openapi
from src.common.session import engine
from src.organizations.routes import router as org_router
from src.payments.routes import router as payments_router
from src.payments.webhooks import router as payments_webhook_router
from src.projects.routes import router as project_router
from src.uploads.routes import router as uploads_router

# Production optimizations
IS_PRODUCTION = os.getenv('ENVIRONMENT', 'development') == 'production'

# Configure logging for production
if IS_PRODUCTION:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ],
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
logger = logging.getLogger(__name__)

# Update the database URL to use the correct format
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace(
    'postgresql://', 'postgresql+asyncpg://'
)

# Remove this line since we're importing engine from common.database
# engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info('Database tables created')
    yield
    # Shutdown
    logger.info('Application shutting down')


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
    default_response_class=ORJSONResponse,
)

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
    uploads_router, prefix=f'{settings.API_V1_STR}/uploads', tags=['uploads']
)

# Custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)
