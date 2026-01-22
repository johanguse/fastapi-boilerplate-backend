#!/bin/bash
# Customize deployment scripts for your project

set -e

echo "🔧 Deployment Scripts Customization"
echo "===================================="
echo ""
echo "This script will update all deployment files with your project details."
echo ""
echo "💡 Current configuration:"
echo "  Project: fastapi-boilerplate"
echo "  Domain: usercenter.app"
echo "  Region: iad"
echo ""
echo "Press Enter to keep current values or type new ones:"
echo ""

# Get project details
read -p "Enter your project name (default: fastapi-boilerplate): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-fastapi-boilerplate}

read -p "Enter your domain (default: usercenter.app): " DOMAIN
DOMAIN=${DOMAIN:-usercenter.app}

read -p "Enter preferred Fly.io region (default: iad): " REGION
REGION=${REGION:-iad}

echo ""
echo "📋 Configuration:"
echo "  Project: $PROJECT_NAME"
echo "  Domain: $DOMAIN"
echo "  Region: $REGION"
echo ""
read -p "Continue with these settings? (y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "❌ Customization cancelled"
    exit 1
fi

# Create app names
STAGING_APP="$PROJECT_NAME-backend-staging"
PROD_APP="$PROJECT_NAME-backend-prod"

echo ""
echo "🔄 Updating deployment scripts..."

# Function to safely replace text in files
safe_replace() {
    local file=$1
    local search=$2
    local replace=$3
    
    if [ -f "$file" ]; then
        # Create backup
        cp "$file" "${file}.bak"
        # Replace text
        sed -i.tmp "s|$search|$replace|g" "$file"
        rm -f "${file}.tmp"
        echo "  ✅ Updated $file"
    else
        echo "  ⚠️  $file not found"
    fi
}

# Update deploy-env.sh
echo "📝 Updating deploy-env.sh..."
safe_replace "deploy-env.sh" "betteragentai-backend-staging" "$STAGING_APP"
safe_replace "deploy-env.sh" "betteragentai-backend-prod" "$PROD_APP"
safe_replace "deploy-env.sh" "betteragentai.com" "$DOMAIN"
safe_replace "deploy-env.sh" "REGION=\"iad\"" "REGION=\"$REGION\""

# Update deploy-multi-container.sh
echo "📝 Updating deploy-multi-container.sh..."
safe_replace "deploy-multi-container.sh" "betteragentai-backend-staging-multi" "${STAGING_APP}-multi"
safe_replace "deploy-multi-container.sh" "betteragentai-backend-prod-multi" "${PROD_APP}-multi"

# Update deploy.sh
echo "📝 Updating deploy.sh..."
safe_replace "deploy.sh" "betteragentai-backend-staging" "$STAGING_APP"
safe_replace "deploy.sh" "betteragentai-backend-prod" "$PROD_APP"
safe_replace "deploy.sh" "betteragentai.com" "$DOMAIN"

# Update setup-custom-domain.sh
echo "📝 Updating setup-custom-domain.sh..."
safe_replace "setup-custom-domain.sh" "betteragentai-backend-staging" "$STAGING_APP"
safe_replace "setup-custom-domain.sh" "betteragentai-backend-prod" "$PROD_APP"
safe_replace "setup-custom-domain.sh" "api-staging.betteragentai.com" "api-staging.$DOMAIN"
safe_replace "setup-custom-domain.sh" "api.betteragentai.com" "api.$DOMAIN"

# Update fly.toml
echo "📝 Updating fly.toml..."
if [ -f "fly.toml" ]; then
    cp "fly.toml" "fly.toml.bak"
    cat > fly.toml << EOF
app = "$PROJECT_NAME-api"
primary_region = "$REGION"

[build]
  dockerfile = "docker/Dockerfile.prod"

[env]
  PORT = "8000"
  PYTHONUNBUFFERED = "1"

[http_service]
  internal_port = 8000
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
    echo "  ✅ Updated fly.toml"
fi

echo ""
echo "✅ Customization complete!"
echo ""
echo "📋 Your apps will be named:"
echo "  Staging: $STAGING_APP"
echo "  Production: $PROD_APP"
echo "  Domains:"
echo "    - Staging: api-staging.$DOMAIN"
echo "    - Production: api.$DOMAIN"
echo ""
echo "📁 Backup files created (.bak) in case you need to revert"
echo ""
echo "🎯 Next steps:"
echo "1. Create .env.staging file with your environment variables"
echo "2. Create .env.production file with your environment variables"
echo "3. Make scripts executable: chmod +x *.sh"
echo "4. Deploy: ./deploy.sh"
echo ""
echo "📖 For more info, see: DEPLOYMENT_SCRIPTS_REVIEW.md"

