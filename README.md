# AI-Powered SaaS Boilerplate (FastAPI)

## Description

This is a comprehensive SaaS boilerplate with AI-powered features including document intelligence, content generation, and analytics. Built with FastAPI, React, and modern AI capabilities.

> **Note**: This backend works with the companion [Frontend](../frontend) project. The frontend also supports an alternative [Bun + Hono backend](../backend_bun_hono) - switch between them using environment variables.

## 🚀 AI Features

- **AI Document Intelligence**: Upload, process, and chat with documents using AI
- **AI Content Generation**: Generate blog posts, emails, social media content, and more
- **AI Analytics**: Natural language queries to generate insights and charts
- **Usage Tracking**: Credit-based billing system with real-time usage monitoring
- **Multi-provider Support**: OpenAI and Anthropic integration

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
- UV (package manager)
- just (task runner)
- Ruff
- Docker
- **AI Integration**: OpenAI, Anthropic, LangChain

## 📚 Documentation

Comprehensive documentation is available in the `/docs` folder:

- **[AI Features Guide](docs/AI_FEATURES.md)** - Complete AI features documentation and API reference
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

### Prerequisites

#### Install UV (Package Manager)

UV is a fast Python package manager. Install it following the [official guide](https://docs.astral.sh/uv/getting-started/installation/):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

#### Install just (Task Runner)

`just` is a command runner for executing project tasks. Install it using one of these methods:

```bash
# Ubuntu/Debian
sudo apt install just

# macOS (Homebrew)
brew install just

# Windows (Scoop)
scoop install just

# Using cargo (Rust)
cargo install just

# Using prebuilt binary (Linux/macOS)
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
```

See the [just installation guide](https://github.com/casey/just#installation) for more options.

### Using UV (without Docker)

1. Clone the repository
2. Copy `.env.example` to `.env` and update the values
3. Run `uv sync` to install dependencies
4. Run `just dev` to start the development server

### Available Commands

Run `just --list` to see all available commands:

| Command | Description |
|---------|-------------|
| `just dev` | Start development server with hot reload |
| `just test` | Run tests with coverage |
| `just lint` | Run linting checks |
| `just format` | Format code with ruff |
| `just migrate` | Run database migrations |
| `just seed` | Seed database with sample data |
| `just reset-and-seed` | Reset database and seed |

**Without `just` installed**, use `uv run` directly:

```bash
# Start dev server
uv run uvicorn src.main:app --reload --port 8000

# Run tests
uv run pytest -s -x --cov=src -vv

# Run migrations
uv run alembic upgrade head

# Seed database
uv run python scripts/run_seed.py
```

### Running with Multiple Workers (Production)

For production or load testing, run with multiple workers:

```bash
# Using Uvicorn (workers and reload are mutually exclusive)
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn (recommended for production)
# Auto-calculates workers based on CPU cores (CPU * 2 + 1)
uv run gunicorn -c gunicorn.conf.py src.main:app

# Or specify workers manually with Gunicorn
uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

> **Note**: Use `--reload` for development (single worker, auto-restart on code changes). Use `--workers` for production (multiple workers, no auto-reload).

### Using Docker

#### Development Environment

1. Copy environment files:

```bash
# From project root
cp docker/.env.example ./.env.docker.dev
cp docker/.env.example ./.env.docker.prod
```

1. Review and update the environment files with your values

2. Run development environment:

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
docker-compose -f docker/docker-compose.yml exec web uv run alembic upgrade head
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

## Database Seeding

Seed the database with sample data for development:

```bash
# Using UV
just seed

# Or directly
uv run python scripts/seed.py

# Using Docker
docker-compose -f docker/docker-compose.yml exec web uv run python scripts/seed.py
```

**Or run fresh seed** (deletes all data first):

   ```bash
   uv run python scripts/seed_fresh.py
   ```

### Seed Data Includes

The seed script creates comprehensive test data:

- **9 Users** with different roles and statuses
- **5 Organizations** with various team structures
- **7 Projects** across different organizations
- **50+ Activity Logs** with diverse actions and timestamps
- **4 Subscription Plans** (Free, Basic, Premium, Enterprise)
- **5 Active Subscriptions** with billing history
- **Multiple Billing Records** spanning several months

### Default User Accounts

All seed users share the same password: **`admin123`**

| Email | Role | Status | Verified | Description |
|-------|------|--------|----------|-------------|
| `admin@example.com` | admin | active | ✓ | Admin with superuser privileges |
| `john@example.com` | member | active | ✓ | Regular active member |
| `jane@example.com` | member | active | ✓ | Regular active member |
| `sarah@example.com` | member | active | ✓ | Regular active member |
| `bob@example.com` | member | invited | ✗ | Recently invited user |
| `alice@example.com` | member | invited | ✗ | Recently invited user |
| `suspended@example.com` | member | suspended | ✓ | Suspended account |
| `mike@example.com` | member | active | ✓ | Recently joined member |
| `emma@example.com` | admin | active | ✓ | Admin without superuser |

### Sample Organizations with Subscriptions

| Organization | Plan | Status | Monthly Cost |
|--------------|------|--------|--------------|
| Development Team | Enterprise | Active | $255.00 |
| Marketing Team | Premium | Active | $68.00 |
| Research Team | Basic | Active | $28.00 |
| Sales Department | Premium | Trialing | $68.00 |
| Customer Success | Free | Active | $0.00 |

## Testing

Run `just test`

For running specific test files:

```bash
# Run all auth tests
just test-auth

# Run a specific test
uv run pytest tests/test_auth.py::test_login_success -v

# Run tests with watch mode (auto-rerun on file changes)
just test-watch
```

### Email Testing

By default, all email sending is **mocked** during tests to prevent spam and speed up test execution. To test with real email sending (e.g., to verify email templates), use the `--with-email` flag:

```bash
# Run tests without sending real emails (default)
uv run pytest

# Run tests and send real emails
uv run pytest --with-email

# Test specific email functionality with real sending
uv run pytest tests/test_email_service.py --with-email -v
```

**Note**: When using `--with-email`, emails will be sent to the addresses specified in your tests. Make sure your `RESEND_API_KEY` is configured and you have a verified domain, or use your own email for testing.

### Testing with SQLAlchemy ORM

When writing tests for FastAPI endpoints that use SQLAlchemy models, you might encounter issues like `UnmappedClassError: Class 'typing.Any' is not mapped`. This is common when trying to instantiate SQLAlchemy models directly in tests.

#### Solutions

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
just format
```

Lint code:

```bash
just lint
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
just migrate
# Or directly:
uv run alembic upgrade head
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
FRONTEND_URL=http://localhost:5173

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

## Deployment

This project uses [Fly.io](https://fly.io) for deployment with separate staging and production environments.

### App Configuration

| Environment | App Name | Config File |
|-------------|----------|-------------|
| Staging | `fastapi-boilerplate-backend-staging` | `fly.staging.toml` |
| Production | `fastapi-boilerplate-backend-prod` | `fly.production.toml` |

### Prerequisites

1. **Install Fly.io CLI**:
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login to Fly.io**:
```bash
flyctl auth login
```

3. **Set up GitHub Secret** (for CI/CD):
   - Get your token: `flyctl auth token`
   - Add `FLY_API_TOKEN` to your GitHub repository secrets

### Quick Deploy

#### Interactive Deployment

```bash
./scripts/deploy/deploy.sh
```

This shows an interactive menu with options for:
- Deploy to Staging
- Deploy to Production
- Setup Custom Domain
- Show deployment status

#### Direct Deployment

```bash
# Deploy to staging (without updating secrets)
./scripts/deploy/deploy-staging.sh

# Deploy to staging and update environment variables
./scripts/deploy/deploy-staging.sh --set-vars

# Deploy to production (requires confirmation)
./scripts/deploy/deploy-production.sh

# Deploy to production and update environment variables
./scripts/deploy/deploy-production.sh --set-vars

# Universal deployment script
./scripts/deploy/deploy-env.sh staging          # Deploy without updating secrets
./scripts/deploy/deploy-env.sh production --set-vars  # Deploy and update secrets
```

#### Understanding `--set-vars` Flag

By default, deployment scripts **skip** updating environment variables to speed up deployments and avoid accidentally overwriting secrets. Use the `--set-vars` flag when you need to:

- **Initial deployment**: First time deploying to set up all secrets
- **Update secrets**: Changed API keys, database URLs, or other environment variables
- **Add new variables**: Added new environment variables to your `.env.*` files

**Without `--set-vars`** (default):
- ✅ Faster deployments (skips secrets update)
- ✅ Safe - won't overwrite existing secrets
- ✅ Use for code-only deployments

**With `--set-vars`**:
- 📋 Loads all variables from `.env.staging` or `.env.production`
- 🔄 Updates all secrets on Fly.io
- ⚠️  Takes longer due to secret updates

### Environment Variables

Create environment files in the backend root (gitignored):

**`.env.staging`** - Staging secrets
**`.env.production`** - Production secrets

Example format:
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=https://staging.yourdomain.com
```

The deployment scripts can automatically load these files when using the `--set-vars` flag:

```bash
# Update staging secrets and deploy
./scripts/deploy/deploy-staging.sh --set-vars

# Deploy without updating secrets (faster)
./scripts/deploy/deploy-staging.sh
```

**Note**: On first deployment, use `--set-vars` to set up all secrets. For subsequent code-only deployments, omit the flag for faster deploys.

### Manual Secrets Setup

If you prefer setting secrets manually:

```bash
# Set individual secrets
flyctl secrets set DATABASE_URL="postgresql://user:pass@host:5432/db" --app fastapi-boilerplate-backend-staging

# Set multiple secrets at once
flyctl secrets set \
  DATABASE_URL="postgresql://..." \
  SECRET_KEY="..." \
  JWT_SECRET="..." \
  --app fastapi-boilerplate-backend-staging
```

### Custom Domain Setup

```bash
./scripts/deploy/setup-custom-domain.sh staging
# or
./scripts/deploy/setup-custom-domain.sh production
```

Then add DNS records to your domain:

**CNAME (recommended for subdomains)**:
```
Type: CNAME
Name: api-staging
Target: fastapi-boilerplate-backend-staging.fly.dev
```

### Post-Deployment

After deploying, run migrations:

```bash
# SSH into the app and run migrations
flyctl ssh console -a fastapi-boilerplate-backend-staging -C 'uv run alembic upgrade head'
```

### Monitoring

```bash
# Check app status
flyctl status --app fastapi-boilerplate-backend-staging

# View logs
flyctl logs --app fastapi-boilerplate-backend-staging

# SSH into the app
flyctl ssh console --app fastapi-boilerplate-backend-staging
```

### CI/CD

The GitHub Actions workflow (`.github/workflows/fly-deploy.yml`) automatically deploys to staging when pushing to the `main` branch. Make sure `FLY_API_TOKEN` is set in your repository secrets.

### Alternative: Railway

Railway is also supported via `railway.toml`, `nixpacks.toml`, and `Dockerfile.railway` — see the [Production Deployment Guide](docs/production-deployment.md#-deployment-to-railway) for setup steps.

### Environment Variables (Production)

- Production secrets are stored in Fly.io using `flyctl secrets set`
- CI/CD secrets are stored in GitHub Actions Secrets
- Development variables are in `.env` (local)
- Staging/Production variables in `.env.staging` / `.env.production`

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
