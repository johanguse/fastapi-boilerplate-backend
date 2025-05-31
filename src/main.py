import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from src.auth.routes import router as auth_router
from src.auth.user_routes import router as user_router
from src.common.config import settings
from src.common.database import Base
from src.common.health import router as health_router
from src.common.middleware import add_logging_middleware
from src.common.openapi import custom_openapi
from src.common.session import engine
from src.projects.routes import router as project_router
from src.teams.routes import router as team_router

# Configure logging
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
)

# Add middleware
add_logging_middleware(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

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
    user_router,
    prefix=settings.API_V1_STR,
)
app.include_router(
    team_router, prefix=f'{settings.API_V1_STR}/teams', tags=['teams']
)
app.include_router(
    project_router, prefix=f'{settings.API_V1_STR}/projects', tags=['projects']
)

# Custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)
