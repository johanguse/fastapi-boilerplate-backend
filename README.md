# FastAPI Boilerplate

A modern, production-ready FastAPI boilerplate with Poetry, Alembic, Docker, PostgreSQL, and comprehensive authentication using Domain-Driven Design (DDD) architecture.

> [!TIP]
> If your project is going to be bigger, I suggest reading the [FastAPI Beyond CRUD](https://jod35.github.io/fastapi-beyond-crud-docs/site/chapter4/)

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Domain-Driven Design** - Clean architecture with domain separation
- **Poetry** - Dependency management and packaging
- **Alembic** - Database migrations
- **PostgreSQL** - Production-ready database with async support
- **Docker & Docker Compose** - Containerization for development and deployment
- **JWT Authentication** - Secure token-based authentication
- **Email Services** - Email verification and password reset using Resend
- **Comprehensive Testing** - Pytest with async support
- **Code Quality** - Ruff for linting and formatting, mypy for type checking
- **Task Management** - Taskipy for common development tasks
- **Database Models** - Users, Teams, and Projects with relationships
- **CORS Support** - Cross-origin resource sharing
- **Logging & Monitoring** - Structured logging with correlation IDs

## Project Structure

```
FastAPI-Boilerplate/
├── src/
│   ├── main.py                      # Application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # Configuration management
│   ├── common/                      # Shared utilities
│   │   ├── __init__.py
│   │   ├── models.py                # Base models (TimestampedModel, Base)
│   │   ├── database.py              # Database session management
│   │   └── enums.py                 # Shared enumerations
│   ├── auth/                        # Authentication domain
│   │   ├── __init__.py
│   │   ├── models.py                # User model
│   │   ├── schemas.py               # Pydantic schemas
│   │   ├── service.py               # Business logic
│   │   ├── dependencies.py          # FastAPI dependencies
│   │   └── router.py                # API endpoints
│   ├── teams/                       # Teams domain
│   │   ├── __init__.py
│   │   └── router.py                # Team endpoints (placeholder)
│   └── projects/                    # Projects domain
│       ├── __init__.py
│       └── router.py                # Project endpoints (placeholder)
├── alembic/                         # Database migrations
├── scripts/
│   └── init_db.py                   # Database initialization script
├── tests/                           # Test suite
├── docker-compose.yml               # Docker services
├── Dockerfile                       # Application container
├── pyproject.toml                   # Poetry configuration
├── alembic.ini                      # Alembic configuration
└── .pre-commit-config.yaml          # Pre-commit hooks
```

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Docker and Docker Compose (optional)
- PostgreSQL (if not using Docker)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FastAPI-Boilerplate
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp example.env .env
   # Edit .env with your configuration
   ```

4. **Start the database (using Docker)**
   ```bash
   docker-compose up -d db
   ```

5. **Run database migrations**
   ```bash
   poetry run task db-upgrade
   ```

6. **Initialize database with admin user (optional)**
   ```bash
   poetry run task init-db
   ```

7. **Start the application**
   ```bash
   poetry run task dev
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Using Docker Compose

For a complete development environment:

```bash
docker-compose up
```

This will start:
- FastAPI application on port 8000
- PostgreSQL database on port 5432
- Test database on port 5433

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `RESEND_API_KEY` | Resend API key for emails | Optional |
| `FROM_EMAIL` | From email address | `noreply@example.com` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | `30` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["http://localhost:3000"]` |

## Development Commands

This project uses Taskipy for common development tasks. Here are the available commands:

### Application
```bash
poetry run task dev              # Start development server with hot reload
```

### Testing
```bash
poetry run task test             # Run tests
poetry run task test-cov         # Run tests with coverage report
```

### Code Quality
```bash
poetry run task lint             # Check code with Ruff
poetry run task lint-fix         # Fix auto-fixable issues with Ruff
poetry run task format           # Format code with Ruff
poetry run task format-check     # Check if code is formatted
poetry run task type-check       # Run mypy type checking
poetry run task quality          # Run all quality checks
poetry run task quality-fix      # Fix all auto-fixable issues
```

### Database
```bash
poetry run task db-upgrade       # Apply database migrations
poetry run task db-downgrade     # Rollback last migration
poetry run task db-revision      # Create new migration
poetry run task init-db          # Initialize database with admin user
```

### Utilities
```bash
poetry run task clean            # Clean Python cache files
poetry run task pre-commit-install # Install pre-commit hooks
```

## Database Migrations

Create a new migration:
```bash
poetry run task db-revision -m "Description of changes"
```

Apply migrations:
```bash
poetry run task db-upgrade
```

Rollback migrations:
```bash
poetry run task db-downgrade
```

## API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user profile
- `PUT /auth/me` - Update user profile

### Teams (Placeholder)

- Team management endpoints (to be implemented)

### Projects (Placeholder)

- Project management endpoints (to be implemented)

## Testing

Run the test suite:
```bash
poetry run task test
```

Run tests with coverage:
```bash
poetry run task test-cov
```

Run specific test categories:
```bash
poetry run pytest -m unit
poetry run pytest -m integration
```

## Code Quality

The project uses Ruff for both linting and formatting, providing fast and comprehensive code quality checks.

### Linting and Formatting
```bash
# Check code quality
poetry run task quality

# Fix auto-fixable issues
poetry run task quality-fix

# Individual commands
poetry run task lint             # Check for issues
poetry run task lint-fix         # Fix auto-fixable issues
poetry run task format           # Format code
poetry run task format-check     # Check formatting
poetry run task type-check       # Type checking with mypy
```

### Ruff Configuration

Ruff is configured in `pyproject.toml` with the following features:
- **Linting**: Comprehensive rule set including pycodestyle, pyflakes, isort, bugbear, comprehensions, pyupgrade, unused arguments, simplify, pathlib, eradicate, pylint, naming, and print detection
- **Formatting**: Black-compatible code formatting
- **Import sorting**: Automatic import organization
- **Type checking**: Integration with mypy for static type analysis

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:
```bash
poetry run task pre-commit-install
```

This will run Ruff linting and formatting on every commit.

## Domain-Driven Design Architecture

This project follows DDD principles with clear domain separation:

### Common Domain
- **Base Models**: Shared database models and utilities
- **Database**: Session management and connection handling
- **Enums**: Shared enumerations across domains

### Auth Domain
- **Models**: User authentication and authorization
- **Schemas**: Pydantic models for API requests/responses
- **Service**: Business logic for authentication
- **Dependencies**: FastAPI dependency injection
- **Router**: API endpoints for authentication

### Teams Domain (Extensible)
- Ready for team management functionality
- Follows the same pattern as auth domain

### Projects Domain (Extensible)
- Ready for project management functionality
- Follows the same pattern as auth domain

## Database Models

### User (Auth Domain)
- Authentication and user management
- Roles: USER, ADMIN
- Email verification and password reset capabilities
- Timestamped model with created_at and updated_at

### Team (Teams Domain - To be implemented)
- Team organization
- Owner relationship with users
- Team member management

### Project (Projects Domain - To be implemented)
- Project management within teams
- Belongs to a team

## Development

### Adding New Domains

1. Create a new domain directory in `src/`
2. Follow the established pattern:
   ```
   src/new_domain/
   ├── __init__.py
   ├── models.py          # SQLAlchemy models
   ├── schemas.py         # Pydantic schemas
   ├── service.py         # Business logic
   ├── dependencies.py    # FastAPI dependencies
   └── router.py          # API endpoints
   ```
3. Register the router in `src/main.py`
4. Create database migration with Alembic
5. Add tests in `tests/`

### Best Practices

- Use async/await for I/O operations
- Implement proper error handling
- Add comprehensive tests
- Follow RESTful API design
- Use dependency injection
- Validate all inputs with Pydantic
- Log important events
- Use transactions for data consistency
- Follow DDD principles with clear domain boundaries

## Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up Resend API key
- [ ] Configure CORS origins
- [ ] Set up SSL/TLS
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Run security audit
- [ ] Set up pre-commit hooks

### Docker Production

Build production image:
```bash
docker build -t fastapi-boilerplate .
```

Run with production settings:
```bash
docker run -e ENV_STATE=prod -p 8000:8000 fastapi-boilerplate
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks: `poetry run task quality`
6. Install and run pre-commit hooks: `poetry run task pre-commit-install`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
