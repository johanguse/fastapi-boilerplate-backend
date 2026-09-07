#!/bin/bash

# Function to load environment variables from a file and set them as Fly.io secrets
# Usage: load_env_file <env_file_path> <app_name>

load_env_file() {
    local ENV_FILE=$1
    local APP_NAME=$2

    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ Environment file $ENV_FILE not found"
        return 1
    fi

    echo "📋 Setting secrets for $APP_NAME from $ENV_FILE..."

    local SECRETS_LIST=()

    # Read each line, skip comments and empty lines
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Ignore lines starting with # or empty lines
        if [[ ! "$line" =~ ^# && ! -z "$line" ]]; then
            # Trim whitespace
            line=$(echo "$line" | xargs)
            
            # Extract key and value
            # Split at the first '='
            KEY=$(echo "$line" | cut -d '=' -f 1)
            VALUE=$(echo "$line" | cut -d '=' -f 2-)
            
            # Remove quotes if present
            VALUE=$(echo "$VALUE" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

            if [ -n "$KEY" ] && [ -n "$VALUE" ]; then
                SECRETS_LIST+=("$KEY=$VALUE")
            fi
        fi
    done < "$ENV_FILE"

    if [ ${#SECRETS_LIST[@]} -gt 0 ]; then
        echo "🔄 Setting ${#SECRETS_LIST[@]} secrets at once..."
        flyctl secrets set "${SECRETS_LIST[@]}" --app "$APP_NAME"
    else
        echo "⚠️ No secrets found to set."
    fi

    echo "✅ All secrets from $ENV_FILE have been set for $APP_NAME"
}