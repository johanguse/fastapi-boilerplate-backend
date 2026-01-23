#!/bin/bash

# Deploy script for STAGING environment - FastAPI Boilerplate Backend

set -e

echo "🚀 Deploying FastAPI Boilerplate Backend to STAGING"

# Configuration
APP_NAME="fastapi-boilerplate-backend-staging"
REGION="iad"
CONFIG_FILE="fly.staging.toml"
ENV_FILE=".env.staging"

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

# Check if staging app exists, if not create it
echo "🔍 Checking if staging app exists..."
if ! flyctl apps list | grep -q "$APP_NAME"; then
    echo "📱 Staging app doesn't exist. Creating new app..."
    flyctl apps create "$APP_NAME"
else
    echo "✅ Staging app already exists"
fi

# Check if .env.staging exists and load it
if [ -f "$ENV_FILE" ]; then
    echo "🔧 Found $ENV_FILE file"
    echo "📋 Loading STAGING environment variables from $ENV_FILE..."
    
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
echo "✅ STAGING deployment complete!"
echo "🔗 URL: https://$APP_NAME.fly.dev"
echo ""
echo "🎯 Next steps:"
echo "1. Run migrations: flyctl ssh console -a $APP_NAME -C 'uv run alembic upgrade head'"
echo "2. Setup custom domain: ./scripts/deploy/setup-custom-domain.sh staging"
