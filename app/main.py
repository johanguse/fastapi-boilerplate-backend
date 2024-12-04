import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.core.config import settings
from app.core.database import Base, engine
from app.core.openapi import custom_openapi
from app.routers import blog, project, team, user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info('Database tables created')
    yield
    # Shutdown
    logger.info('Application shutting down')


app = FastAPI(title=settings.PROJECT_NAME, version='1.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

add_pagination(app)

app.include_router(user.router, prefix=settings.API_V1_STR)
app.include_router(
    team.router, prefix=f'{settings.API_V1_STR}/teams', tags=['teams']
)
app.include_router(
    project.router, prefix=f'{settings.API_V1_STR}/projects', tags=['projects']
)
app.include_router(
    blog.router,
    prefix=f'{settings.API_V1_STR}/blog',
    tags=['blog'],
)

app.openapi = lambda: custom_openapi(app)
