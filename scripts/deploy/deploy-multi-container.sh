#!/bin/bash

# Deploy script for multi-container setup with Docker Compose

set -e

echo "🚀 Deploying Better Agent AI with Multi-Container Setup"

# Check Fly.io version
echo "🔍 Checking Fly.io version..."
FLY_VERSION=$(flyctl version | grep flyctl | awk '{print $2}' | cut -d'v' -f2)
echo "Current Fly.io version: v$FLY_VERSION"

# Parse version (simplified check)
MAJOR=$(echo $FLY_VERSION | cut -d'.' -f1)
MINOR=$(echo $FLY_VERSION | cut -d'.' -f2)
PATCH=$(echo $FLY_VERSION | cut -d'.' -f3)

# Check if version is >= 0.3.149
if [ "$MAJOR" -eq 0 ] && [ "$MINOR" -eq 3 ] && [ "$PATCH" -lt 149 ]; then
    echo "⚠️  Fly.io version v0.3.149 or later is required for Docker Compose support"
    echo "Run: fly version upgrade"
    exit 1
fi

echo "✅ Fly.io version is compatible with Docker Compose"

# Check if compose file exists
if [ ! -f "docker/docker-compose.yml" ]; then
    echo "❌ Docker Compose file not found at docker/docker-compose.yml"
    echo "Please ensure you have the compose file configured"
    exit 1
fi

# Choose environment
echo ""
echo "Choose deployment environment:"
echo "1) Staging (fastapi-boilerplate-backend-staging-multi)"
echo "2) Production (fastapi-boilerplate-backend-prod-multi)"
echo ""
read -p "Enter your choice (1-2): " choice

case $choice in
    1)
        APP_NAME="fastapi-boilerplate-backend-staging-multi"
        ENV="staging"
        ;;
    2)
        APP_NAME="fastapi-boilerplate-backend-prod-multi"
        ENV="production"
        # Production confirmation
        echo "⚠️  You are about to deploy to PRODUCTION with multi-container setup!"
        read -p "Are you sure you want to continue? (y/N): " confirm
        if [[ $confirm != [yY] ]]; then
            echo "❌ Production deployment cancelled"
            exit 1
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Backup current fly.toml if it exists
if [ -f "fly.toml" ]; then
    cp fly.toml fly.toml.backup
    echo "📋 Backed up current fly.toml"
fi

# Create multi-container fly.toml
echo "🔧 Creating multi-container fly.toml configuration..."

cat > fly.toml << EOF
app = "$APP_NAME"
primary_region = "iad"

[build]
  dockerfile = "docker/Dockerfile.prod"
  # Enable this for Docker Compose multi-container
  # compose = "docker/docker-compose.prod.yml"

[env]
  PORT = "8000"
  PYTHONUNBUFFERED = "1"
  ENVIRONMENT = "$ENV"

[http_service]
  internal_port = 8000
  # Change to 8080 when using NGINX reverse proxy
  # internal_port = 8080
  force_https = true
  auto_stop_machines = "off"
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

[http_service.concurrency]
  type = "connections"
  hard_limit = 50
  soft_limit = 40

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/api/v1/health"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024

[deploy]
  strategy = "rolling"
EOF

# Check if app exists, if not create it
echo "🔍 Checking if multi-container app exists..."
if ! flyctl status --app $APP_NAME &> /dev/null; then
    echo "📱 App doesn't exist. Creating new multi-container app..."
    flyctl launch --no-deploy --name $APP_NAME --region iad --config fly.toml
else
    echo "✅ App already exists"
fi

# Load environment variables if env file exists
ENV_FILE=".env.$ENV"
if [ -f "$ENV_FILE" ]; then
    echo "📋 Loading environment variables from $ENV_FILE..."
    
    # Source the load-env function if it exists
    if [ -f "./load-env.sh" ]; then
        source ./load-env.sh
        load_env_file "$ENV_FILE" "$APP_NAME"
    else
        echo "⚠️  load-env.sh not found, please set environment variables manually"
    fi
fi

# Option to enable Docker Compose
echo ""
echo "🐳 Docker Compose Configuration:"
echo "1) Deploy with single container (default)"
echo "2) Deploy with Docker Compose (PostgreSQL + Qdrant + Redis)"
echo ""
read -p "Enter your choice (1-2): " compose_choice

if [ "$compose_choice" = "2" ]; then
    echo "🔧 Configuring for Docker Compose multi-container deployment..."
    
    # Update fly.toml for compose
    sed -i.tmp 's/# compose = "docker\/docker-compose.prod.yml"/compose = "docker\/docker-compose.prod.yml"/g' fly.toml
    sed -i.tmp 's/dockerfile = "docker\/Dockerfile.prod"/# dockerfile = "docker\/Dockerfile.prod"/g' fly.toml
    sed -i.tmp 's/internal_port = 8000/internal_port = 8080/g' fly.toml
    
    # Remove temporary file
    rm -f fly.toml.tmp
    
    echo "📋 Updated fly.toml for multi-container deployment"
    
    # Show what will be deployed
    echo ""
    echo "🚀 Will deploy with:"
    echo "  - FastAPI backend (app:8000)"
    echo "  - PostgreSQL database (postgres:5432)"
    echo "  - Qdrant vector database (qdrant:6333)"
    echo "  - Redis for caching (redis:6379)"
    echo "  - NGINX reverse proxy (nginx:8080)"
fi

# Deploy the application
echo ""
echo "🚀 Deploying $ENV multi-container application..."
flyctl deploy --config fly.toml --app $APP_NAME

echo ""
echo "✅ Multi-container deployment complete!"
echo ""

if [ "$compose_choice" = "2" ]; then
    echo "🐳 Your application now includes:"
    echo "  - FastAPI backend with User Center features"
    echo "  - PostgreSQL for user data and teams"
    echo "  - Qdrant for vector search and RAG"
    echo "  - Redis for caching and rate limiting"
    echo "  - NGINX reverse proxy with load balancing"
else
    echo "📦 Your application is running with:"
    echo "  - FastAPI backend (single container)"
    echo "  - External database connections"
fi

echo ""
echo "🔗 Access your application at:"
echo "  https://$APP_NAME.fly.dev"
echo "🔗 Health check: https://$APP_NAME.fly.dev/api/v1/health"
echo ""
echo "📊 Monitor with:"
echo "  flyctl logs --app $APP_NAME"
echo "  flyctl status --app $APP_NAME"
echo ""

if [ -f "fly.toml.backup" ]; then
    echo "🔙 To revert to previous configuration:"
    echo "  cp fly.toml.backup fly.toml && flyctl deploy --app $APP_NAME"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Test all endpoints: https://$APP_NAME.fly.dev/docs"
echo "2. Set up custom domain with multi-container app"
echo "3. Monitor performance and scaling"