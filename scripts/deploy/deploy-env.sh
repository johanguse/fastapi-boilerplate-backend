#!/bin/bash

# Universal deployment script that uses environment-specific .env files

set -e

echo "🚀 Environment-based Deployment for Better Agent AI"

# Default values
SET_VARS=false

# Parse command-line arguments
ENVIRONMENT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --set-vars)
            SET_VARS=true
            shift
            ;;
        staging|production)
            ENVIRONMENT=$1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 <environment> [--set-vars]"
            echo "Example: $0 staging"
            echo "Example: $0 production --set-vars"
            echo "  --set-vars    Update environment variables from .env file"
            exit 1
            ;;
    esac
done

# Check if environment was provided
if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment> [--set-vars]"
    echo "Example: $0 staging"
    echo "Example: $0 production --set-vars"
    exit 1
fi

# Validate environment
case $ENVIRONMENT in
    staging)
        APP_NAME="fastapi-boilerplate-backend-staging"
        CONFIG_FILE="fly.staging.toml"
        ENV_FILE=".env.staging"
        REGION="iad"
        ;;
    production)
        APP_NAME="fastapi-boilerplate-backend-prod"
        CONFIG_FILE="fly.production.toml"
        ENV_FILE=".env.production"
        REGION="iad"
        ;;
    *)
        echo "❌ Invalid environment: $ENVIRONMENT"
        echo "Valid environments: staging, production"
        exit 1
        ;;
esac

echo "🔧 Deploying to $ENVIRONMENT environment"
echo "📱 App: $APP_NAME"
echo "📄 Config: $CONFIG_FILE"
echo "🌍 Region: $REGION"
echo "📋 Environment file: $ENV_FILE"

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

# Production confirmation
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  You are about to deploy to PRODUCTION!"
    read -p "Are you sure you want to continue? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "❌ Production deployment cancelled"
        exit 1
    fi
fi

# Check if app exists, if not create it
echo "🔍 Checking if $ENVIRONMENT app exists..."
if ! flyctl status --app $APP_NAME &> /dev/null; then
    echo "📱 App doesn't exist. Creating new app..."
    flyctl launch --no-deploy --name $APP_NAME --region $REGION --config $CONFIG_FILE
else
    echo "✅ App already exists"
fi

# Only set secrets when --set-vars is passed
if [ "$SET_VARS" = true ]; then
    if [ -f "$ENV_FILE" ]; then
        echo "📋 Loading environment variables from $ENV_FILE..."
        
        # Source the load-env function if it exists
        if [ -f "./load-env.sh" ]; then
            source ./load-env.sh
            load_env_file "$ENV_FILE" "$APP_NAME"
        else
            echo "📋 Setting environment variables manually..."
            # Read .env file and set secrets
            while IFS='=' read -r key value; do
                # Skip comments and empty lines
                [[ $key =~ ^[[:space:]]*# ]] && continue
                [[ -z $key ]] && continue
                
                # Remove quotes from value if present
                value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
                
                echo "Setting $key..."
                flyctl secrets set "$key=$value" --app $APP_NAME
            done < "$ENV_FILE"
        fi
    else
        echo "❌ Environment file $ENV_FILE not found"
        echo "Please create $ENV_FILE with your environment variables"
        echo ""
        echo "Example $ENV_FILE content:"
        echo "DATABASE_URL=postgresql://user:pass@host:5432/dbname"
        echo "JWT_SECRET=your-secret-key"
        echo "OPENAI_API_KEY=your-openai-key"
        echo "QDRANT_URL=https://your-qdrant-cluster.qdrant.cloud:6333"
        echo "QDRANT_API_KEY=your-qdrant-api-key"
        exit 1
    fi
else
    echo "⏭️  Skipping secrets update (use --set-vars to update environment variables)"
fi

# Deploy the application
echo "🚀 Deploying $ENVIRONMENT application..."
flyctl deploy --config $CONFIG_FILE --app $APP_NAME

echo "✅ $ENVIRONMENT deployment complete!"
echo "🔗 Fly.io URL: https://$APP_NAME.fly.dev"
echo "🔗 Health check: https://$APP_NAME.fly.dev/api/v1/health"

# Show custom domain info
if [ "$ENVIRONMENT" = "staging" ]; then
    echo "🌐 Setup custom domain: api-staging.usercenter.app"
elif [ "$ENVIRONMENT" = "production" ]; then
    echo "🌐 Setup custom domain: api.usercenter.app"
fi

# Show next steps
echo ""
echo "🎯 Next steps:"
echo "1. Set up custom domain: ./setup-custom-domain.sh"
echo "2. Check logs: flyctl logs --app $APP_NAME"
echo "3. Monitor status: flyctl status --app $APP_NAME"
echo "4. Test API: curl https://$APP_NAME.fly.dev/api/v1/health"