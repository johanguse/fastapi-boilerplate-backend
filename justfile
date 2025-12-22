# justfile for backend development commands
# Run `just --list` to see all available commands

# Default recipe - show available commands
default:
    @just --list

# Linting
lint:
    uv run ruff check src && uv run ruff check src --diff

# Format and fix code
format:
    uv run ruff check src --fix && uv run ruff format src

# Check formatting without making changes
format-check:
    uv run ruff format src --check

# Type checking (placeholder)
type-check:
    @echo "No type checking configured"

# Start development server
run:
    uv run uvicorn src.main:app --reload --port 8000

# Alias for run
dev: run

# Run all tests with coverage
test: lint
    uv run pytest -s -x --cov=src --cov-config=pyproject.toml -vv

# Run tests with HTML and XML coverage reports
test-cov:
    uv run pytest --cov=src --cov-config=pyproject.toml --cov-report=html --cov-report=xml

# Run authentication tests only
test-auth:
    uv run pytest tests/test_auth.py -v

# Run tests in watch mode
test-watch:
    uv run pytest -xvs --watch

# Create new Alembic migration (usage: just migrations "description")
migrations message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Apply pending migrations
migrate:
    uv run alembic upgrade head

# Seed the database
seed:
    uv run python scripts/seed.py

# Reset the database
reset-db:
    uv run python scripts/reset_db.py

# Reset database and seed
reset-and-seed: reset-db seed

# Install dependencies
install:
    uv sync

# Install with dev dependencies
install-dev:
    uv sync --group dev

# Update dependencies
update:
    uv lock --upgrade

# Show outdated packages
outdated:
    uv pip list --outdated

# Clean cache and build artifacts
clean:
    rm -rf .pytest_cache .coverage htmlcov coverage.xml .ruff_cache __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
