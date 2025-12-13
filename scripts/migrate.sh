#!/bin/bash
# FlipRadar Database Migration Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 FlipRadar Database Migration${NC}"
echo "=================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${POSTGRES_USER:-flipradar}
DB_PASSWORD=${POSTGRES_PASSWORD:-flipradar_secret}
DB_NAME=${POSTGRES_DB:-flipradar}

# Check if running in Docker
if [ "$1" == "--docker" ]; then
    echo -e "${YELLOW}Running migrations in Docker...${NC}"
    docker-compose -f docker/docker-compose.yml exec -T postgres psql -U $DB_USER -d $DB_NAME -f /docker-entrypoint-initdb.d/init.sql
else
    echo -e "${YELLOW}Running migrations locally...${NC}"

    # Check if psql is available
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}Error: psql is not installed. Please install PostgreSQL client.${NC}"
        exit 1
    fi

    # Run the init SQL
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f docker/init-db.sql
fi

echo -e "${GREEN}✅ Migration completed successfully!${NC}"
