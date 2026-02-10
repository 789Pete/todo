#!/usr/bin/env bash
set -euo pipefail

echo "=== Todo App Development Setup ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "Python $PYTHON_VERSION OK"

# Check uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
echo "uv $(uv --version) OK"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
fi

# Install dependencies
echo "Installing development dependencies..."
uv pip sync requirements/development.txt

# Setup .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    # Generate a random secret key
    SECRET_KEY=$(.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-secret-key-here/$SECRET_KEY/" .env
    else
        sed -i "s/your-secret-key-here/$SECRET_KEY/" .env
    fi
    echo ".env created with generated SECRET_KEY"
fi

# Validate Django configuration
echo "Running Django checks..."
.venv/bin/python manage.py check

# Run migrations
echo "Running migrations..."
.venv/bin/python manage.py migrate

# Create superuser
echo ""
echo "Create a superuser account (optional, Ctrl+C to skip):"
.venv/bin/python manage.py createsuperuser || true

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
.venv/bin/pre-commit install

echo ""
echo "=== Setup Complete ==="
echo "Activate the virtual environment: source .venv/bin/activate"
echo "Run the server: python manage.py runserver"
