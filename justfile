# justfile for backend development commands
# Run `just --list` to see all available commands

# Default recipe - show available commands
default:
    @just --list

# ============================================================================
# Development
# ============================================================================

# Start development server
run:
    uv run uvicorn src.main:app --reload --port 8000

# Alias for run
dev: run

# ============================================================================
# Code Quality
# ============================================================================

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

# ============================================================================
# Testing - Basic
# ============================================================================

# Run all tests with coverage (stops on first failure)
test: lint
    uv run pytest -s -x --cov=src --cov-config=pyproject.toml -vv

# Run all tests without stopping on failure
test-all:
    uv run pytest -s --cov=src --cov-config=pyproject.toml -vv

# Run tests quickly without coverage
test-fast:
    uv run pytest -x -q

# ============================================================================
# Testing - Failed/Specific
# ============================================================================

# Run only failed tests from last run
test-failed:
    uv run pytest --lf -v

# Run failed tests first, then remaining
test-failed-first:
    uv run pytest --ff -v

# Run tests matching a keyword (usage: just test-match "keyword")
test-match keyword:
    uv run pytest -k "{{keyword}}" -v

# ============================================================================
# Testing - By Module
# ============================================================================

# Run authentication tests
test-auth:
    uv run pytest tests/test_auth.py tests/test_auth_better_auth.py tests/test_auth_enhanced.py tests/auth/ -v

# Run organization tests
test-org:
    uv run pytest tests/test_organization.py tests/organizations/ -v

# Run project tests
test-project:
    uv run pytest tests/test_project.py tests/projects/ -v

# Run onboarding tests
test-onboarding:
    uv run pytest tests/test_onboarding.py -v

# Run payment tests
test-payments:
    uv run pytest tests/payments/ -v

# Run security tests
test-security:
    uv run pytest tests/test_security.py tests/test_security_edgecases.py tests/security/ -v

# Run common/utils tests
test-common:
    uv run pytest tests/common/ -v

# ============================================================================
# Testing - Special Modes
# ============================================================================

# Run tests with real email sending (for testing email templates)
test-with-email:
    uv run pytest --with-email -v

# Run tests in watch mode (auto-rerun on file changes)
test-watch:
    uv run pytest -xvs --watch

# Run tests with HTML and XML coverage reports
test-cov:
    uv run pytest --cov=src --cov-config=pyproject.toml --cov-report=html --cov-report=xml

# Show coverage report in terminal
test-cov-report:
    uv run pytest --cov=src --cov-config=pyproject.toml --cov-report=term-missing

# ============================================================================
# Database
# ============================================================================

# Create new Alembic migration (usage: just migrations "description")
migrations message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Apply pending migrations
migrate:
    uv run alembic upgrade head

# Seed the database
seed:
    uv run python scripts/seed/seed.py

# Reset the database
reset-db:
    uv run python scripts/reset_db.py

# Reset database and seed
reset-and-seed: reset-db seed

# ============================================================================
# Dependencies
# ============================================================================

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

# ============================================================================
# Cleanup
# ============================================================================

# Clean cache and build artifacts
clean:
    rm -rf .pytest_cache .coverage htmlcov coverage.xml .ruff_cache __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
