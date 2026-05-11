#!/bin/bash
# Axeng - Start Next.js UI from root directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_DIR="$SCRIPT_DIR/ui/nextjs"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Axeng Next.js UI...${NC}"
echo ""

# Check if setup has been run
if [ ! -d "$UI_DIR/node_modules" ]; then
    echo -e "${YELLOW}⚠️  First time setup required!${NC}"
    echo ""
    echo -e "Running setup (this will take ~2 minutes)..."
    cd "$UI_DIR"
    ./setup.sh
    echo ""
fi

# Start the UI
cd "$UI_DIR"
exec ./start.sh
