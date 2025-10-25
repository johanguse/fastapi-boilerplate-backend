#!/bin/bash

# Function to load environment variables from .env files to Fly.io secrets

load_env_file() {
    local env_file=$1
    local app_name=$2
    
    if [ ! -f "$env_file" ]; then
        echo "❌ Environment file $env_file not found"
        return 1
    fi
    
    echo "📋 Setting secrets from $env_file for app $app_name..."
    
    # Create temporary file for batch secret setting
    temp_secrets_file=$(mktemp)
    
    # Process .env file
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z $key ]] && continue
        
        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Remove quotes from value if present
        value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
        
        # Add to secrets file
        echo "$key=$value" >> "$temp_secrets_file"
        
    done < "$env_file"
    
    # Set all secrets at once (more efficient)
    if [ -s "$temp_secrets_file" ]; then
        echo "🔐 Setting $(wc -l < "$temp_secrets_file") environment variables..."
        flyctl secrets import --app "$app_name" < "$temp_secrets_file"
    else
        echo "⚠️  No environment variables found in $env_file"
    fi
    
    # Clean up
    rm -f "$temp_secrets_file"
    
    echo "✅ Environment variables loaded successfully"
}