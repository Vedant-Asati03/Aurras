#!/bin/bash
set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Aurras publication process...${NC}"

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
poetry install

# Build the package
echo -e "${GREEN}Building the package...${NC}"
poetry build

# Check PyPI authentication
echo -e "${YELLOW}Checking PyPI authentication...${NC}"
if ! poetry config pypi-token.pypi &> /dev/null; then
    echo -e "${RED}PyPI token not found!${NC}"
    echo -e "${YELLOW}Please set up your PyPI token with:${NC}"
    echo -e "   ${GREEN}poetry config pypi-token.pypi \"your-token-here\"${NC}"
    echo -e "${YELLOW}You can generate a token at: https://pypi.org/manage/account/token/${NC}"
    
    read -p "Do you want to enter your PyPI token now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your PyPI token: " token
        poetry config pypi-token.pypi "$token"
        echo -e "${GREEN}Token configured!${NC}"
    else
        echo -e "${RED}Publication aborted. Token required for publishing.${NC}"
        exit 1
    fi
fi

# Verify the user wants to publish
read -p "Do you want to publish to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Publish to PyPI
    echo -e "${GREEN}Publishing to PyPI...${NC}"
    poetry publish
    
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
    echo -e "${GREEN}You can publish later with: poetry publish${NC}"
fi

# Make the package executable locally for testing
echo -e "${GREEN}Making Aurras executable locally...${NC}"
poetry install

echo -e "${GREEN}You can now run Aurras with: poetry run aurras${NC}"
