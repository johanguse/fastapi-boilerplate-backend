# Project Management API

## Description

This is a project management API that allows you to manage users, organizations, and projects.

## Technologies

- FastAPI
- FastAPI Users
- FastAPI Security
- FastAPI Pagination
- SQLAlchemy
- Alembic
- PostgreSQL
- Uvicorn
- Pytest
- Poetry
- Ruff
- Docker

## 📚 Documentation

Comprehensive documentation is available in the `/docs` folder:

- **[Production Deployment Guide](docs/production-deployment.md)** - Complete production setup and deployment instructions
- **[Performance Optimization Guide](docs/performance-optimization.md)** - Detailed performance optimizations and benchmarks
- **[Monitoring & Metrics Guide](docs/monitoring-metrics.md)** - Real-time monitoring and performance tracking
- **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - Development roadmap and features
- **[i18n Integration](docs/i18n-integration.md)** - Internationalization setup and usage

## ⚡ Performance Features

This boilerplate includes production-ready performance optimizations:

- **20-50% faster JSON responses** with ORJSON
- **2-4x better throughput** under high concurrency with uvloop
- **40% faster HTTP parsing** with httptools  
- **80-90% bandwidth reduction** with GZip compression
- **Memory-efficient streaming** for large data exports
- **Real-time performance monitoring** with detailed metrics
- **Dependency caching** for expensive operations

## Local Development Setup

### Using Poetry (without Docker)

1. Clone the repository
2. Copy `.env.example` to `.env` and update the values
3. Run `poetry shell`
4. Run `poetry install`
5. Run `task run`

### Using Docker

#### Development Environment

1. Copy environment files:

```bash
# From project root
cp docker/.env.example ./.env.docker.dev
cp docker/.env.example ./.env.docker.prod
```

2. Review and update the environment files with your values

3. Run development environment:

```bash
# Start the services
docker-compose -f docker/docker-compose.yml --project-directory . up --build

# Run in detached mode
docker-compose -f docker/docker-compose.yml --project-directory . up -d --build

# View logs
docker-compose -f docker/docker-compose.yml --project-directory . logs -f

# Stop services
docker-compose -f docker/docker-compose.yml --project-directory . down

# Access the application:
# - API: http://localhost:8000
# - Documentation: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

#### Production Environment

1. Run production environment:

```bash
# Start the services
docker-compose -f docker/docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.prod.yml down
```

### Docker Commands

#### Basic Commands

Monitor containers:

```bash
# View logs
docker logs -f fastapi-dev

# Check container status
docker ps

# Stop container
docker stop fastapi-dev

# Remove container
docker rm fastapi-dev

# Remove image
docker rmi fastapi-app-dev
```

#### Database Commands

```bash
# Access database
docker-compose -f docker/docker-compose.yml exec db psql -U postgres

# Run migrations
docker-compose -f docker/docker-compose.yml exec web poetry run alembic upgrade head
```

#### Stop and Clean Up

Stop all containers:

```bash
# Stop all running containers
docker stop $(docker ps -a -q)

# Remove all stopped containers
docker rm $(docker ps -a -q)

# Remove all volumes
docker volume prune -f
```

Stop project containers:

```bash
# Development environment
COMPOSE_PROJECT_NAME=usercenter docker compose -f docker/docker-compose.yml down -v

# Production environment
COMPOSE_PROJECT_NAME=usercenter docker compose -f docker/docker-compose.prod.yml down -v
```

#### View Logs

```bash
# Development
docker compose -f docker/docker-compose.yml logs -f

# Production
docker compose -f docker/docker-compose.prod.yml logs -f
```

### Notes

- Development environment mounts your local code as a volume, so changes are reflected immediately
- Production environment builds a new image with your code, so you need to rebuild to see changes
- Database data is persisted in Docker volumes, so it survives container restarts
- Always use secure passwords in production environment

## Testing

Run `task test`

For running specific test files:
```bash
# Run all auth tests
task test-auth

# Run a specific test
poetry run pytest tests/test_auth.py::test_login_success -v

# Run tests with watch mode (auto-rerun on file changes)
task test-watch
```

### Testing with SQLAlchemy ORM

When writing tests for FastAPI endpoints that use SQLAlchemy models, you might encounter issues like `UnmappedClassError: Class 'typing.Any' is not mapped`. This is common when trying to instantiate SQLAlchemy models directly in tests.

#### Solutions:

1. **Use Mock Objects**: Instead of real SQLAlchemy models, create simple mock classes:
   ```python
   class MockUser:
       def __init__(self, **kwargs):
           for key, value in kwargs.items():
               setattr(self, key, value)
   ```

2. **Mock Dependency Injection**: Override FastAPI dependencies:
   ```python
   async def override_dependency():
       return mock_object
   
   app.dependency_overrides[original_dependency] = override_dependency
   ```

3. **Mock HTTP Responses**: For complete isolation, mock the HTTP client itself:
   ```python
   mock_response = Response(
       status_code=200,
       content=json.dumps(response_data).encode(),
       headers={"Content-Type": "application/json"}
   )
   
   # Store and restore the original method
   original_request = client.get
   client.get = mock_get_function
   # ...test code...
   client.get = original_request
   ```

4. **Clean Up After Tests**: Always restore original dependencies and methods:
   ```python
   try:
       # Test code
   finally:
       # Restore original dependencies/methods
   ```

## Code Quality

Format code:

```bash
task format
```

Lint code:

```bash
task lint
```

## Database Management

### Clean Database

Delete all data from the database:

```sql
DROP TABLE IF EXISTS "public"."activity_logs" CASCADE;
DROP TABLE IF EXISTS "public"."alembic_version" CASCADE;
DROP TABLE IF EXISTS "public"."organization_invitations" CASCADE;
DROP TABLE IF EXISTS "public"."organization_members" CASCADE;
DROP TABLE IF EXISTS "public"."organizations" CASCADE;
DROP TABLE IF EXISTS "public"."projects" CASCADE;
DROP TABLE IF EXISTS "public"."users" CASCADE;

-- If your DB has legacy types from earlier versions
DROP TYPE IF EXISTS teammemberrole;
DROP TYPE IF EXISTS modelstatus;
DROP TYPE IF EXISTS invitationstatus;
```

### Migrations

Remove all alembic migrations:

```bash
rm -f alembic/versions/*.py
```

Create new migration:

```bash
alembic revision --autogenerate -m "initial"
```

Upgrade database:

```bash
poetry run alembic upgrade head
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# App
PROJECT_NAME=FastAPI App
PROJECT_VERSION=0.1.0
API_V1_STR=/api/v1

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres

# Security
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
JWT_LIFETIME_SECONDS=3600

# Email
RESEND_API_KEY=your-resend-api-key
RESEND_FROM_EMAIL=your-email@domain.com

# Frontend
FRONTEND_URL=http://localhost:3000

# Better Auth (optional)
BETTER_AUTH_ENABLED=false
BETTER_AUTH_ALGORITHM=RS256
BETTER_AUTH_JWKS_URL=
BETTER_AUTH_SHARED_SECRET=
BETTER_AUTH_ISSUER=
BETTER_AUTH_AUDIENCE=
BETTER_AUTH_EMAIL_CLAIM=email
BETTER_AUTH_SUB_IS_EMAIL=false
```

### Authentication

By default, the API uses FastAPI Users (HS256 JWT, audience `fastapi-users:auth`).

Optionally, you can accept Better Auth tokens side-by-side by configuring the env vars above. The unified dependency `get_current_active_user` in `src/common/security.py` will validate either:

- FastAPI Users JWT using `JWT_SECRET`
- Better Auth JWT via JWKS (RS256) or shared secret (HS256), with optional issuer/audience checks

User lookup is performed by email (from `sub` if `BETTER_AUTH_SUB_IS_EMAIL=true`, else from `BETTER_AUTH_EMAIL_CLAIM`, default `email`).

## Organizations API quickstart

Base path: `/api/v1/organizations`

Create organization:

```http
POST /api/v1/organizations
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Acme Inc"
}
```

List my organizations (paginated):

```http
GET /api/v1/organizations?page=1&size=50
Authorization: Bearer <token>
```

Invite a member:

```http
POST /api/v1/organizations/{organization_id}/invite
Authorization: Bearer <token>
Content-Type: application/json

{
    "email": "teammate@example.com",
    "role": "member"
}
```

## Todo

- Add tests
- Add documentation
- Add <https://www.literalai.com/>

## Additional Notes

- Never commit `.env` files to version control
- Use different environment variables for development and production
- Always use HTTPS in production
- Regularly update dependencies and base images
- Monitor container logs and health checks in production

## Deployment

### Fly.io Deployment

1. Install the Fly.io CLI:

```bash
curl -L https://fly.io/install.sh | sh
```

1. Login to Fly.io:

```bash
fly auth login
```

1. Create a new app:

```bash
fly apps create your-app-name
```

1. Set up secrets:

```bash
flyctl secrets set DATABASE_URL="postgresql://user:pass@host:5432/db"
flyctl secrets set SECRET_KEY="your-secret-key"
flyctl secrets set JWT_SECRET="your-jwt-secret"
flyctl secrets set RESEND_API_KEY="your-resend-api-key"
flyctl secrets set RESEND_FROM_EMAIL="your-email@domain.com"
```

1. Deploy:

```bash
fly deploy
```

### Environment Variables (Production)

- Production secrets are stored in Fly.io using `flyctl secrets set`
- CI/CD secrets are stored in GitHub Actions Secrets
- Development variables are in `.env.docker.dev`
- Production variables template in `.env.docker.prod`

## API Documentation

The API documentation is available at the following endpoints:

### Development

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

### Production

- Swagger UI: <https://your-domain.com/docs>
- ReDoc: <https://your-domain.com/redoc>
- OpenAPI JSON: <https://your-domain.com/openapi.json>

Note: Replace `your-domain.com` with your actual production domain.
