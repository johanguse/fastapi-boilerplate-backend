# Use Python 3.11 since that's what's specified in pyproject.toml
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for psycopg2-binary
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy only requirements files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .

EXPOSE 8000

# Define environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application using uvicorn
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

# Add after EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health -H "accept: application/json" || exit 1