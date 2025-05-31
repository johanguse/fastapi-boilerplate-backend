# Docker Setup

This directory contains all Docker-related files for the project.

## File Structure

- `Dockerfile` - Development Docker configuration
- `Dockerfile.prod` - Production Docker configuration
- `docker-compose.yml` - Development Docker Compose configuration
- `docker-compose.prod.yml` - Production Docker Compose configuration
- `.env.example` - Example environment variables for Docker

## Usage

### Development

```bash
# Start development environment
docker-compose -f docker/docker-compose.yml --project-directory . up --build

# Access the application at:
# - API: http://localhost:8000
# - Documentation: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc

# View logs
docker-compose -f docker/docker-compose.yml --project-directory . logs -f

# Stop services
docker-compose -f docker/docker-compose.yml --project-directory . down
```

### Production

```bash
# Start production environment
docker-compose -f docker/docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.prod.yml down
```

## Environment Variables

1. Copy the example environment file:

```bash
cp docker/.env.example docker/.env.docker.dev
cp docker/.env.example docker/.env.docker.prod
```

2. Update the values in both files according to your environment.

   - `SECRET_KEY` - A secret key for JWT.
   - `ALGORITHM` - The algorithm to use for JWT.
   - `ACCESS_TOKEN_EXPIRE_MINUTES` - The expiration time for access tokens.
   - `REFRESH_TOKEN_EXPIRE_MINUTES` - The expiration time for refresh tokens.

3. Run the development environment:

```bash
docker-compose -f docker/docker-compose.yml --project-directory . up --build
```

4. Access the application at:

- API: <http://localhost:8000>
- Documentation: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
