#!/bin/bash

# Master Deployment Script for Better Agent AI
# This script organizes all deployment options in one place

set -e

echo "🚀 Better Agent AI Deployment"
echo "================================="
echo ""

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

echo "Choose your deployment option:"
echo ""
echo "🌍 Environment-based Deployment (Recommended):"
echo "  1) Deploy to Staging (uses .env.staging)"
echo "  2) Deploy to Production (uses .env.production)"
echo ""
echo "🐳 Multi-container Deployment:"
echo "  3) Deploy with Docker Compose (PostgreSQL + Qdrant + Redis)"
echo ""
echo "🌐 Domain Management:"
echo "  4) Setup Custom Domain (Generic)"
echo "  5) Setup Cloudflare DNS + Certificates"
echo ""
echo "🔧 Legacy Scripts:"
echo "  6) Deploy Staging (legacy script)"
echo "  7) Deploy Production (legacy script)" 
echo ""
echo "ℹ️  Information:"
echo "  8) Show deployment status"
echo "  9) View deployment guide"
echo "  10) Exit"
echo ""

read -p "Enter your choice (1-10): " choice

case $choice in
    1)
        echo ""
        echo "🔵 Deploying to STAGING environment..."
        echo "Using: .env.staging → betteragentai-backend-staging"
        echo ""
        ./deploy-env.sh staging
        ;;
    2)
        echo ""
        echo "🔴 Deploying to PRODUCTION environment..."
        echo "Using: .env.production → betteragentai-backend-prod"
        echo ""
        ./deploy-env.sh production
        ;;
    3)
        echo ""
        echo "🐳 Deploying with Multi-container setup..."
        echo "This will deploy with PostgreSQL, Qdrant, and Redis"
        echo ""
        read -p "Continue with multi-container deployment? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            ./deploy-multi-container.sh
        else
            echo "❌ Multi-container deployment cancelled"
        fi
        ;;
    4)
        echo ""
        echo "🌐 Setting up custom domain (generic)..."
        ./setup-custom-domain.sh
        ;;
    5)
        echo ""
        echo "☁️ Setting up Cloudflare DNS + Certificates..."
        ./cloudflare-setup.sh
        ;;
    6)
        echo ""
        echo "🔵 Running legacy staging deployment..."
        ./deploy-staging.sh
        ;;
    7)
        echo ""
        echo "🔴 Running legacy production deployment..."
        ./deploy-production.sh
        ;;
    8)
        echo ""
        echo "📊 Current Deployment Status:"
        echo ""
        
        # Check staging
        echo "🔵 STAGING:"
        if flyctl status --app fastapi-boilerplate-backend-staging &> /dev/null; then
            echo "  ✅ App exists: fastapi-boilerplate-backend-staging"
            echo "  🔗 Fly.io URL: https://fastapi-boilerplate-backend-staging.fly.dev"
            echo "  🌐 Custom URL: https://api-staging.usercenter.app"
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
            echo "  🌐 Custom URL: https://api.usercenter.app"
            flyctl status --app fastapi-boilerplate-backend-prod | grep "Status:"
        else
            echo "  ❌ Production app not deployed"
        fi
        
        echo ""
        echo "Run 'flyctl apps list' to see all your apps"
        ;;
    9)
        echo ""
        echo "📖 Deployment Guide:"
        echo ""
        if [ -f "README-ENV.md" ]; then
            echo "📄 Environment-based deployment guide:"
            echo "   cat README-ENV.md"
        fi
        
        if [ -f "DEPLOYMENT.md" ]; then
            echo "📄 Full deployment guide:"
            echo "   cat DEPLOYMENT.md"
        fi
        
        if [ -f "CLOUDFLARE-GUIDE.md" ]; then
            echo "☁️ Cloudflare setup guide:"
            echo "   cat CLOUDFLARE-GUIDE.md"
        fi
        
        echo ""
        echo "🔧 Available scripts in this directory:"
        ls -la *.sh 2>/dev/null | grep -E "(deploy|setup|cloudflare)" | awk '{print "   " $9 " - " $5 " bytes"}' || echo "   No deployment scripts found"
        ;;
    10)
        echo ""
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid choice. Please run the script again and choose 1-10."
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment completed!"
echo ""
echo "🎯 Quick next steps:"
echo "1. Test your deployment: curl https://your-app.fly.dev/api/v1/health"
echo "2. View logs: flyctl logs --app your-app-name"
echo "3. Set up custom domain: ./deploy.sh and choose option 4"
echo "4. Monitor: flyctl status --app your-app-name"