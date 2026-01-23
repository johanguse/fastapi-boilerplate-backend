#!/bin/bash

# Custom Domain Setup for FastAPI Boilerplate Backend

set -e

echo "🌐 Setting up custom domain for FastAPI Boilerplate Backend"

# Check if environment argument is provided
ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
    echo "Select environment:"
    echo "1) Staging (fastapi-boilerplate-backend-staging)"
    echo "2) Production (fastapi-boilerplate-backend-prod)"
    read -p "Enter choice (1 or 2): " env_choice
    
    case $env_choice in
      1) ENVIRONMENT="staging" ;;
      2) ENVIRONMENT="production" ;;
      *) echo "❌ Invalid choice"; exit 1 ;;
    esac
fi

case $ENVIRONMENT in
  staging)
    APP_NAME="fastapi-boilerplate-backend-staging"
    SUGGESTED_DOMAIN="api-staging.yourdomain.com"
    ;;
  production)
    APP_NAME="fastapi-boilerplate-backend-prod"
    SUGGESTED_DOMAIN="api.yourdomain.com"
    ;;
  *)
    echo "❌ Invalid environment: $ENVIRONMENT"
    exit 1
    ;;
esac

read -p "Enter custom domain (suggested: $SUGGESTED_DOMAIN): " CUSTOM_DOMAIN
CUSTOM_DOMAIN=${CUSTOM_DOMAIN:-$SUGGESTED_DOMAIN}

echo "🔧 Adding certificate for $CUSTOM_DOMAIN..."

# Add certificate
flyctl certs create "$CUSTOM_DOMAIN" --app "$APP_NAME"

echo "📋 Certificate created! Now add these DNS records to your domain provider:"
echo ""
echo "Option 1: CNAME (recommended for subdomains)"
echo "  Type: CNAME"
echo "  Name: $(echo $CUSTOM_DOMAIN | cut -d'.' -f1)"
echo "  Target: $APP_NAME.fly.dev"
echo ""
echo "Option 2: A Record (direct IP)"
echo "  Type: A"
echo "  Name: $(echo $CUSTOM_DOMAIN | cut -d'.' -f1)"
echo "  Value: [Get IPv4 from 'flyctl ips list' below]"
echo ""

# Show current IPs
echo "🔍 Current app IP addresses:"
flyctl ips list --app "$APP_NAME"

echo ""
echo "⏳ Waiting for DNS propagation... It can take up to 24-48 hours, but usually much faster."
echo "Check status with: flyctl certs show $CUSTOM_DOMAIN --app $APP_NAME"
echo ""
echo "Once verified, your backend will be available at: https://$CUSTOM_DOMAIN"