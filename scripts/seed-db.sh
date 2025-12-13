#!/bin/bash
# FlipRadar Database Seed Script
# Populates the database with sample data for development/testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌱 FlipRadar Database Seeding${NC}"
echo "================================="

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

# Create seed SQL
SEED_SQL=$(cat <<'EOF'
-- Seed demo user
INSERT INTO users (email, username, password_hash, full_name, plan, is_active, email_verified, preferences)
VALUES (
    'demo@flipradar.com',
    'demo_user',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.fhAEAIpqd9zKSS', -- password: demo123
    'Demo User',
    'pro',
    true,
    true,
    '{"min_margin": 20, "categories": ["sneakers", "textile"], "sizes": ["42", "43", "M", "L"], "risk_profile": "balanced"}'
)
ON CONFLICT (email) DO NOTHING;

-- Seed sample deals
INSERT INTO deals (
    source_id, external_id, product_name, brand, model, category,
    original_price, sale_price, discount_pct, size, color, product_url, image_url,
    vinted_median, vinted_count, margin_amount, margin_pct, flip_score, status
)
SELECT
    s.id,
    'DEMO-' || generate_series,
    CASE (generate_series % 5)
        WHEN 0 THEN 'Nike Air Max 90'
        WHEN 1 THEN 'Adidas Ultraboost 22'
        WHEN 2 THEN 'Nike Dunk Low Retro'
        WHEN 3 THEN 'Adidas Stan Smith'
        ELSE 'Nike Air Force 1'
    END,
    CASE (generate_series % 2)
        WHEN 0 THEN 'Nike'
        ELSE 'Adidas'
    END,
    CASE (generate_series % 5)
        WHEN 0 THEN 'Air Max 90'
        WHEN 1 THEN 'Ultraboost 22'
        WHEN 2 THEN 'Dunk Low Retro'
        WHEN 3 THEN 'Stan Smith'
        ELSE 'Air Force 1'
    END,
    'sneakers',
    (80 + (generate_series % 100))::numeric,
    (50 + (generate_series % 60))::numeric,
    (20 + (generate_series % 40))::numeric,
    CASE (generate_series % 4)
        WHEN 0 THEN '42'
        WHEN 1 THEN '43'
        WHEN 2 THEN '44'
        ELSE '41'
    END,
    CASE (generate_series % 3)
        WHEN 0 THEN 'Black'
        WHEN 1 THEN 'White'
        ELSE 'Grey'
    END,
    'https://example.com/product/' || generate_series,
    'https://example.com/image/' || generate_series || '.jpg',
    (70 + (generate_series % 50))::numeric,
    (10 + (generate_series % 30)),
    ((70 + (generate_series % 50)) - (50 + (generate_series % 60)))::numeric,
    (((70 + (generate_series % 50)) - (50 + (generate_series % 60)))::numeric / (50 + (generate_series % 60))::numeric * 100)::numeric,
    (50 + (generate_series % 50)),
    'active'
FROM sources s, generate_series(1, 50)
WHERE s.name = 'Nike FR'
LIMIT 50
ON CONFLICT DO NOTHING;

-- Seed popularity reference data
INSERT INTO popularity_reference (brand, model, category, popularity_score, search_volume, trend_direction)
VALUES
    ('Nike', 'Air Max 90', 'sneakers', 95, 150000, 'up'),
    ('Nike', 'Dunk Low', 'sneakers', 98, 200000, 'up'),
    ('Nike', 'Air Force 1', 'sneakers', 92, 180000, 'stable'),
    ('Adidas', 'Stan Smith', 'sneakers', 85, 100000, 'stable'),
    ('Adidas', 'Ultraboost', 'sneakers', 88, 120000, 'up'),
    ('Nike', 'Jordan 1', 'sneakers', 99, 250000, 'up'),
    ('Adidas', 'Yeezy', 'sneakers', 90, 160000, 'down'),
    ('Ralph Lauren', 'Polo', 'textile', 80, 80000, 'stable')
ON CONFLICT (brand, model, category) DO NOTHING;

-- Log seeding
DO $$
BEGIN
    RAISE NOTICE 'Database seeded with demo data!';
END $$;
EOF
)

# Check if running in Docker
if [ "$1" == "--docker" ]; then
    echo -e "${YELLOW}Seeding database in Docker...${NC}"
    echo "$SEED_SQL" | docker-compose -f docker/docker-compose.yml exec -T postgres psql -U $DB_USER -d $DB_NAME
else
    echo -e "${YELLOW}Seeding database locally...${NC}"

    # Check if psql is available
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}Error: psql is not installed. Please install PostgreSQL client.${NC}"
        exit 1
    fi

    echo "$SEED_SQL" | PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
fi

echo -e "${GREEN}✅ Database seeded successfully!${NC}"
echo ""
echo -e "${YELLOW}Demo credentials:${NC}"
echo "  Email: demo@flipradar.com"
echo "  Password: demo123"
