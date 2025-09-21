# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Commands (using taskipy)
- `task run` or `task dev` - Start development server on port 8001
- `task lint` - Run linting with ruff (check only)
- `task format` - Format and fix code with ruff
- `task test` - Run all tests with coverage
- `task test-auth` - Run authentication tests only
- `task test-watch` - Run tests in watch mode
- `task migrations` - Create new Alembic migration (requires message: `task migrations "description"`)
- `task migrate` - Apply pending migrations

### Poetry Commands
- `poetry shell` - Activate virtual environment
- `poetry install` - Install dependencies
- `poetry run uvicorn src.main:app --reload --port 8001` - Direct server start

### Testing Specific Files
```bash
# Run specific test file
poetry run pytest tests/test_auth.py -v

# Run specific test function
poetry run pytest tests/test_auth.py::test_login_success -v
```

### Database Management
- `alembic revision --autogenerate -m "description"` - Create new migration
- `alembic upgrade head` - Apply migrations
- Migrations are stored in `alembic/versions/`

## Architecture Overview

This is a FastAPI-based SaaS boilerplate using Domain-Driven Design (DDD) principles with the following structure:

### Core Architecture
- **FastAPI** with async/await patterns
- **SQLAlchemy 2.0** with async engine (PostgreSQL via asyncpg)
- **Alembic** for database migrations
- **FastAPI Users** for authentication and user management (register, login, reset password, verify email)
- **Pydantic** for data validation and settings management
- **Domain-based module organization** (auth, organizations, projects, activity_log, payments, uploads)

### Module Structure
Each domain module follows this pattern:
```
src/{domain}/
├── __init__.py
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas
├── service.py     # Business logic
└── routes.py      # FastAPI routes
```

### Key Components
- **src/main.py** - Application entry point with router registration
- **src/common/** - Shared utilities, database config, middleware, security
- **src/common/database.py** - SQLAlchemy Base and model imports
- **src/common/config.py** - Pydantic settings with environment variables
- **src/common/session.py** - Database session management

### Database Architecture
- All models inherit from `src.common.database.Base`
- Models are imported in `database.py` to ensure registration
- Async database operations throughout
- Uses dependency injection for database sessions

### Authentication
- **FastAPI Users** integration with OAuth support
- JWT token-based authentication
- User management with organizations and projects relationship
- Role-based access control via organization membership

### Testing Architecture
- **pytest** with async support (pytest-asyncio)
- **testcontainers** for PostgreSQL integration tests
- **factory-boy** for test data generation
- Tests use dependency injection overrides for mocking
- Coverage reporting with pytest-cov

## Environment Configuration

Required environment variables (see README.md for full list):
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Application secret
- `JWT_SECRET` - JWT signing key
- `RESEND_API_KEY` - Email service key
- `STRIPE_SECRET_KEY` - Payment processing
- `RESEND_API_KEY` and `RESEND_FROM_EMAIL` - Email service
- `R2_*` - Cloudflare R2 storage

## Code Quality Standards

- **Ruff** for linting and formatting (line length: 79 characters)
- Single quotes preferred
- Migrations excluded from linting
- Preview features enabled in ruff configuration

## Docker Support

- Development: `docker-compose -f docker/docker-compose.yml up --build`
- Production: `docker-compose -f docker/docker-compose.prod.yml up -d --build`
- Database access: `docker-compose -f docker/docker-compose.yml exec db psql -U postgres`

## Deployment

- **Fly.io** ready with `fly.toml` configuration
- Environment secrets managed via `flyctl secrets set`
- Production builds use multi-stage Docker setup
