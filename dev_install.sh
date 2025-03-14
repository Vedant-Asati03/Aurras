#!/bin/bash
set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Aurras in development mode...${NC}"

# Get absolute project directory path
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo -e "${YELLOW}Project directory: ${PROJECT_DIR}${NC}"

# Clean up any existing installations
echo -e "${YELLOW}Cleaning up any existing installations...${NC}"
pip uninstall -y aurras || true

# Create a simple wrapper script for easy execution
echo -e "${GREEN}Creating aurras command wrapper...${NC}"
mkdir -p "${HOME}/.local/bin"
cat > "${HOME}/.local/bin/aurras" << EOF
#!/bin/bash
# Direct execution from source code
export PYTHONPATH="${PROJECT_DIR}:\${PYTHONPATH}"
exec python3 -m aurras "\$@"
EOF

chmod +x "${HOME}/.local/bin/aurras"

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r "${PROJECT_DIR}/requirements.txt"

# Install spotdl if needed
if ! command -v spotdl &> /dev/null; then
    echo -e "${GREEN}Installing spotdl...${NC}"
    pip install spotdl
fi

echo -e "${GREEN}Setup complete! You can now run 'aurras' directly.${NC}"
echo -e "${GREEN}Any changes to the source code will be immediately available.${NC}"

# Verify installation
if [ -f "${HOME}/.local/bin/aurras" ]; then
    echo -e "${YELLOW}Verification: Command wrapper created at ${HOME}/.local/bin/aurras${NC}"
    echo -e "${GREEN}Try running: aurras --help${NC}"
else
    echo -e "${RED}Warning: Command wrapper could not be created${NC}"
fi

echo -e "${YELLOW}Note: Make sure ${HOME}/.local/bin is in your PATH${NC}"
if [[ ":$PATH:" != *":${HOME}/.local/bin:"* ]]; then
    echo -e "${RED}Warning: ${HOME}/.local/bin is not in your PATH${NC}"
    echo -e "${YELLOW}Add the following line to your ~/.bashrc or ~/.zshrc:${NC}"
    echo -e "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
