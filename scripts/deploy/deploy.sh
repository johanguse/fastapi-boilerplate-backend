#!/bin/bash

# Master Deployment Script for FastAPI Boilerplate Backend
# This script organizes all deployment options in one place

set -e

# Ensure the script is executed with bash (not sh)
if [ -z "$BASH_VERSION" ]; then
    echo "❌ This script must be run with bash. Use: ./deploy.sh (not sh deploy.sh)"
    exit 1
fi

echo "🚀 FastAPI Boilerplate Backend Deployment"
echo "=============================================="
echo ""

# Check if we're in the right directory (scripts/deploy)
# But user might run it from backend root. Let's make it flexible.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../../" # Go to backend root

if [ ! -f "src/main.py" ]; then
    echo "❌ Please ensure you are running this from the backend project structure"
    exit 1
fi

echo "Choose your deployment option:"
echo ""
echo "🌍 Environment-based Deployment:"
echo "  1) Deploy to Staging (uses .env.staging)"
echo "  2) Deploy to Production (uses .env.production)"
echo ""
echo "🌐 Domain Management:"
echo "  3) Setup Custom Domain (Staging or Production)"
echo ""
echo "📊 Information:"
echo "  4) Show deployment status"
echo "  5) Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🔵 Deploying to STAGING environment..."
        ./scripts/deploy/deploy-staging.sh
        ;;
    2)
        echo ""
        echo "🔴 Deploying to PRODUCTION environment..."
        ./scripts/deploy/deploy-production.sh
        ;;
    3)
        echo ""
        echo "🌐 Setting up custom domain..."
        ./scripts/deploy/setup-custom-domain.sh
        ;;
    4)
        echo ""
        echo "📊 Current Deployment Status:"
        echo ""
        
        # Check staging
        echo "🔵 STAGING:"
        if flyctl status --app fastapi-boilerplate-backend-staging &> /dev/null; then
            echo "  ✅ App exists: fastapi-boilerplate-backend-staging"
            echo "  🔗 Fly.io URL: https://fastapi-boilerplate-backend-staging.fly.dev"
            flyctl status --app fastapi-boilerplate-backend-staging | grep "Status:"
        else
            echo "  ❌ Staging app not deployed"
        fi
        
        echo ""
        
        # Check production
        echo "🔴 PRODUCTION:"
        if flyctl status --app fastapi-boilerplate-backend-prod &> /dev/null; then
            echo "  ✅ App exists: fastapi-boilerplate-backend-prod"
            echo "  🔗 Fly.io URL: https://fastapi-boilerplate-backend-prod.fly.dev"
            flyctl status --app fastapi-boilerplate-backend-prod | grep "Status:"
        else
            echo "  ❌ Production app not deployed"
        fi
        
        echo ""
        echo "Run 'flyctl apps list' to see all your apps"
        ;;
    5)
        echo ""
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid choice."
        exit 1
        ;;
esac

echo ""
echo "✅ Operation completed!"