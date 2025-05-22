#!/bin/bash
# setup_dev_env.sh - Set up development environment using uv

# Create a virtual environment using uv
echo "Creating virtual environment using uv..."
uv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install project dependencies
echo "Installing project dependencies..."
uv pip install -r requirements.txt

# Install development packages for testing and formatting
echo "Installing development packages..."
uv pip install pytest black isort flake8 mypy

# Install the package in development mode
echo "Installing package in development mode..."
uv pip install -e .

echo "Development environment setup complete!"
echo "To activate the environment, run: source .venv/bin/activate"
