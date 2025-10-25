#!/bin/bash

# Setup custom domain for Fly.io apps

set -e

echo "🌐 Custom Domain Setup for Better Agent AI"
echo "============================================="

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

echo ""
echo "Choose your app:"
echo "1) Staging (betteragentai-backend-staging)"
echo "2) Production (betteragentai-backend-prod)"
echo "3) Custom app name"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        APP_NAME="fastapi-boilerplate-backend-staging"
        SUGGESTED_DOMAIN="api-staging.usercenter.app"
        ;;
    2)
        APP_NAME="fastapi-boilerplate-backend-prod"
        SUGGESTED_DOMAIN="api.usercenter.app"
        ;;
    3)
        read -p "Enter your app name: " APP_NAME
        read -p "Enter your domain: " SUGGESTED_DOMAIN
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Verify app exists
if ! flyctl status --app $APP_NAME &> /dev/null; then
    echo "❌ App $APP_NAME does not exist or you don't have access"
    exit 1
fi

read -p "Enter your custom domain (default: $SUGGESTED_DOMAIN): " DOMAIN
DOMAIN=${DOMAIN:-$SUGGESTED_DOMAIN}

echo ""
echo "🔧 Setting up domain: $DOMAIN for app: $APP_NAME"

# Add certificate for the domain
echo "📋 Creating certificate for $DOMAIN..."
flyctl certs create --app $APP_NAME $DOMAIN

# Get certificate info
echo ""
echo "📊 Certificate status:"
flyctl certs show --app $APP_NAME $DOMAIN

echo ""
echo "✅ Custom domain setup initiated!"
echo ""
echo "🎯 Next steps:"
echo "1. Add the following DNS records to your domain provider:"
echo ""

# Get app info to show IP addresses
APP_INFO=$(flyctl info --app $APP_NAME)
if echo "$APP_INFO" | grep -q "IPv4"; then
    IPV4=$(echo "$APP_INFO" | grep "IPv4" | awk '{print $2}')
    echo "   A    $DOMAIN    $IPV4"
fi

if echo "$APP_INFO" | grep -q "IPv6"; then
    IPV6=$(echo "$APP_INFO" | grep "IPv6" | awk '{print $2}')
    echo "   AAAA $DOMAIN    $IPV6"
fi

echo ""
echo "2. Wait for DNS propagation (up to 24 hours)"
echo "3. Check certificate status: flyctl certs show --app $APP_NAME $DOMAIN"
echo "4. Test your domain: curl https://$DOMAIN/api/v1/health"
echo ""
echo "📚 Need help? Check the Fly.io docs: https://fly.io/docs/networking/custom-domain/"