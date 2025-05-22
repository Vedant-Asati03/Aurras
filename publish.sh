#!/bin/bash
set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Aurras publication process...${NC}"

# Check if build tools are installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv not found. Installing...${NC}"
    curl -sSf https://astral.sh/uv/install.sh | sh
fi

if ! command -v build &> /dev/null; then
    echo -e "${YELLOW}build package not found. Installing...${NC}"
    uv pip install build
fi

if ! command -v twine &> /dev/null; then
    echo -e "${YELLOW}twine not found. Installing...${NC}"
    uv pip install twine
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
uv pip install -r requirements.txt

# Build the package
echo -e "${GREEN}Building the package...${NC}"
python -m build

# Check PyPI authentication
echo -e "${YELLOW}Checking PyPI authentication...${NC}"
if [ ! -f ~/.pypirc ]; then
    echo -e "${RED}PyPI credentials not found!${NC}"
    echo -e "${YELLOW}Please set up your PyPI credentials in ~/.pypirc or use environment variables for twine.${NC}"
    echo -e "${YELLOW}See: https://twine.readthedocs.io/en/latest/#environment-variables${NC}"
    
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Publication aborted.${NC}"
        exit 1
    fi
fi

# Verify the user wants to publish
read -p "Do you want to publish to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Publish to PyPI
    echo -e "${GREEN}Publishing to PyPI...${NC}"
    twine upload dist/*
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Aurras has been published to PyPI!${NC}"
        echo -e "${GREEN}Users can now install it with: pip install aurras${NC}"
    else
        echo -e "${RED}Publication failed!${NC}"
        echo -e "${YELLOW}Please check your PyPI credentials and try again.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Publication cancelled.${NC}"
    echo -e "${GREEN}You can publish later with: twine upload dist/*${NC}"
fi

# Make the package executable locally for testing
echo -e "${GREEN}Making Aurras executable locally...${NC}"
uv pip install -e .

echo -e "${GREEN}You can now run Aurras with: aurras${NC}"
