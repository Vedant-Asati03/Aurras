#!/bin/bash
set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Aurras in development mode...${NC}"

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${GREEN}Poetry not found. Installing...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Ensure we're using the latest poetry
poetry self update

# Ensure poetry is using the correct environment
echo -e "${GREEN}Configuring Poetry environment...${NC}"
poetry config virtualenvs.in-project true

# Remove any existing installations and clean build artifacts
echo -e "${YELLOW}Cleaning up any existing installations...${NC}"
pip uninstall -y aurras || true
rm -rf dist/ build/ *.egg-info/ || true

# Install in proper development mode
echo -e "${GREEN}Installing Aurras in development mode...${NC}"
poetry install

# Install with pip in editable mode to ensure it's properly linked
echo -e "${GREEN}Creating symlinks for development...${NC}"
pip install -e .

echo -e "${GREEN}Setup complete! You can now run 'aurras' directly without rebuilding.${NC}"
echo -e "${GREEN}Any changes to the code will be immediately available.${NC}"

# Display where the command is being executed from
echo -e "${YELLOW}Verifying installation...${NC}"
which aurras
python -c "import aurras; print(f'Package location: {aurras.__file__}')"
