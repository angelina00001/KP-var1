#!/bin/bash
# Script to run development environment

set -e

echo "🚀 Starting 2FA Service in development mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Start Docker services
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose -f docker/docker-compose.yml up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Run migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Start FastAPI server
echo "🌟 Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000