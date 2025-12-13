#!/bin/bash
# FlipRadar Quick Start Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║           FlipRadar Quick Start           ║"
echo "║     Resell Intelligence Platform MVP      ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if .env exists in docker folder
if [ ! -f docker/.env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp docker/.env.example docker/.env
    echo -e "${YELLOW}⚠️  Please edit docker/.env with your API keys before starting.${NC}"
    echo ""
    read -p "Press Enter to continue after editing .env, or Ctrl+C to cancel..."
fi

echo -e "${GREEN}Starting FlipRadar services...${NC}"
echo ""

# Start Docker containers
cd docker
docker-compose up -d

echo ""
echo -e "${GREEN}✅ FlipRadar is starting up!${NC}"
echo ""
echo "Services:"
echo -e "  ${BLUE}API:${NC}      http://localhost:8000"
echo -e "  ${BLUE}Web:${NC}      http://localhost:3000"
echo -e "  ${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"

# Wait for services
sleep 5

# Check health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${YELLOW}⏳ API is still starting...${NC}"
fi

echo ""
echo -e "${GREEN}To view logs:${NC} docker-compose -f docker/docker-compose.yml logs -f"
echo -e "${GREEN}To stop:${NC} docker-compose -f docker/docker-compose.yml down"
echo ""
echo -e "${BLUE}Demo account:${NC}"
echo "  Email: demo@flipradar.com"
echo "  Password: demo123"
echo ""
echo -e "${GREEN}Happy flipping! 🚀${NC}"
