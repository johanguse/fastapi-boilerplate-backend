#!/bin/bash

# Deploy script for PRODUCTION environment - FastAPI Boilerplate Backend

set -e

echo "🚀 Deploying FastAPI Boilerplate Backend to PRODUCTION"

# Configuration
APP_NAME="fastapi-boilerplate-backend-prod"
REGION="iad"
CONFIG_FILE="fly.production.toml"
ENV_FILE=".env.production"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in to Fly.io
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run: flyctl auth login"
    exit 1
fi

# Confirmation prompt for production
echo "⚠️  You are about to deploy to PRODUCTION ($APP_NAME)!"
read -p "Are you sure you want to continue? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ Production deployment cancelled"
    exit 1
fi

# Check if production app exists, if not create it
echo "🔍 Checking if production app exists..."
if ! flyctl apps list | grep -q "$APP_NAME"; then
    echo "📱 Production app doesn't exist. Creating new app..."
    flyctl apps create "$APP_NAME"
else
    echo "✅ Production app already exists"
fi

# Check if .env.production exists and load it
if [ -f "$ENV_FILE" ]; then
    echo "🔧 Found $ENV_FILE file"
    echo "📋 Loading PRODUCTION environment variables from $ENV_FILE..."
    
    # Source the load-env function
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    source "$SCRIPT_DIR/load-env.sh"
    
    # Load environment variables
    load_env_file "$ENV_FILE" "$APP_NAME"
else
    echo "⚠️  $ENV_FILE file not found. Skipping secrets setup."
    echo "   Please create $ENV_FILE or set secrets manually."
fi

# Deploy the application
echo "🚀 Deploying application..."
flyctl deploy --config "$CONFIG_FILE" --app "$APP_NAME" --remote-only

echo ""
echo "✅ PRODUCTION deployment complete!"
echo "🔗 URL: https://$APP_NAME.fly.dev"
echo ""
echo "🎯 Next steps:"
echo "1. Run migrations: flyctl ssh console -a $APP_NAME -C 'uv run alembic upgrade head'"
echo "2. Setup custom domain: ./scripts/deploy/setup-custom-domain.sh production"
