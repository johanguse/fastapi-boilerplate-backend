#!/bin/bash

# Create environment files
cp docker/.env.example .env.docker.dev
cp docker/.env.example .env.docker.prod

# Create necessary directories
mkdir -p docker/postgres-data

echo "Docker environment files created successfully!"
echo "Please update the environment variables in .env.docker.dev and .env.docker.prod" 