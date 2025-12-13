#!/bin/bash
# FlipRadar Development Mode Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║      FlipRadar Development Mode           ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Navigate to project root
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}Starting database services with Docker...${NC}"
    cd docker
    docker-compose up -d postgres redis
    cd ..
    echo -e "${YELLOW}Waiting for databases...${NC}"
    sleep 3
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo -e "${GREEN}Starting database services with Docker Compose V2...${NC}"
    cd docker
    docker compose up -d postgres redis
    cd ..
    echo -e "${YELLOW}Waiting for databases...${NC}"
    sleep 3
else
    echo -e "${YELLOW}⚠️  Docker not found. Make sure PostgreSQL and Redis are running locally:${NC}"
    echo -e "   ${BLUE}PostgreSQL:${NC} localhost:5432 (user: postgres, password: postgres, db: sellshark)"
    echo -e "   ${BLUE}Redis:${NC}      localhost:6379"
    echo ""
    echo -e "${YELLOW}Install via Homebrew:${NC}"
    echo "   brew install postgresql@15 redis"
    echo "   brew services start postgresql@15"
    echo "   brew services start redis"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $API_PID 2>/dev/null || true
    kill $WEB_PID 2>/dev/null || true
}
trap cleanup EXIT

# Start API in background
echo -e "${GREEN}Starting API server...${NC}"
cd apps/api
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

export DATABASE_URL="postgresql+asyncpg://moussa@localhost:5432/sellshark"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="dev-secret-key"
export APP_ENV="development"

uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!
cd ../..

# Start Web in background
echo -e "${GREEN}Starting Web server...${NC}"
cd apps/web
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
fi

npm run dev &
WEB_PID=$!
cd ../..

echo ""
echo -e "${GREEN}✅ Development servers are running!${NC}"
echo ""
echo "Services:"
echo -e "  ${BLUE}API:${NC}      http://localhost:8000"
echo -e "  ${BLUE}Web:${NC}      http://localhost:3000"
echo -e "  ${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for any process to exit
wait
