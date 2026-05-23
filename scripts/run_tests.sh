#!/bin/bash
# Script to run all tests with coverage

set -e

echo "🔍 Running SAST analysis..."
bandit -r app/ -f json -o bandit_report.json || true
safety check --full-report

echo ""
echo "🧪 Running unit tests..."
pytest tests/ \
    --cov=app \
    --cov-report=term \
    --cov-report=html \
    --cov-report=xml \
    -v \
    --asyncio-mode=auto

echo ""
echo "📊 Coverage report generated in htmlcov/index.html"

echo ""
echo "✅ All checks passed!"