#!/bin/bash
# Axeng - Development mode with live output

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Axeng in development mode...${NC}"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Dependencies not installed. Running setup...${NC}"
    ./setup.sh
    echo ""
fi

# Function to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    pkill -P $$ || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Starting services...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📡 API:${NC}  http://localhost:3457"
echo -e "${BLUE}🌐 UI:${NC}   http://localhost:3000"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start API backend
echo -e "${YELLOW}[API]${NC} Starting..."
python3 api_server.py &
API_PID=$!

# Wait for API to be ready
sleep 2

# Start Next.js
echo ""
echo -e "${YELLOW}[NEXT]${NC} Starting..."
npm run dev

# Wait for processes
wait
