#!/bin/bash
# Axeng - Start both API backend and Next.js UI

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Axeng UI...${NC}"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Dependencies not installed. Running setup...${NC}"
    ./setup.sh
    echo ""
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$NEXT_PID" ]; then
        kill $NEXT_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start API backend in background
echo -e "${BLUE}Starting API backend on port 3457...${NC}"
python3 api_server.py > /tmp/axeng-api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✅ API running (PID: $API_PID)${NC}"

# Wait a bit for API to start
sleep 2

# Start Next.js in background
echo -e "${BLUE}Starting Next.js UI on port 3000...${NC}"
npm run dev > /tmp/axeng-nextjs.log 2>&1 &
NEXT_PID=$!
echo -e "${GREEN}✅ Next.js running (PID: $NEXT_PID)${NC}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Axeng UI is ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BLUE}🌐 UI:${NC}  http://localhost:3000"
echo -e "  ${BLUE}📡 API:${NC} http://localhost:3457/api/health"
echo ""
echo -e "  ${YELLOW}Logs:${NC}"
echo -e "    API:  tail -f /tmp/axeng-api.log"
echo -e "    Next: tail -f /tmp/axeng-nextjs.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Wait for both processes
wait
