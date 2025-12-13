-- FlipRadar Database Initialization
-- This script runs on first database creation

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE user_plan AS ENUM ('free', 'starter', 'pro', 'agency');
CREATE TYPE deal_status AS ENUM ('new', 'active', 'sold', 'expired');
CREATE TYPE alert_channel AS ENUM ('discord', 'email', 'both');
CREATE TYPE outcome_status AS ENUM ('pending', 'purchased', 'sold', 'cancelled');

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url TEXT NOT NULL,
    scraper_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    rate_limit_per_minute INTEGER DEFAULT 60,
    last_scrape_at TIMESTAMP WITH TIME ZONE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) UNIQUE,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    plan user_plan DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    discord_webhook TEXT,
    email_alerts BOOLEAN DEFAULT true,
    alert_threshold INTEGER DEFAULT 70,
    preferences JSONB DEFAULT '{"min_margin": 20, "categories": [], "sizes": [], "risk_profile": "balanced"}',
    daily_alerts_sent INTEGER DEFAULT 0,
    last_alert_reset DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Deals table
CREATE TABLE IF NOT EXISTS deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id),
    external_id VARCHAR(255),
    product_name TEXT NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(255),
    category VARCHAR(100),
    original_price NUMERIC(10, 2),
    sale_price NUMERIC(10, 2) NOT NULL,
    discount_pct NUMERIC(5, 2),
    currency VARCHAR(10) DEFAULT 'EUR',
    size VARCHAR(50),
    color VARCHAR(100),
    condition VARCHAR(50) DEFAULT 'new',
    product_url TEXT NOT NULL,
    image_url TEXT,
    available BOOLEAN DEFAULT true,
    stock_quantity INTEGER,
    vinted_median NUMERIC(10, 2),
    vinted_min NUMERIC(10, 2),
    vinted_max NUMERIC(10, 2),
    vinted_count INTEGER DEFAULT 0,
    margin_amount NUMERIC(10, 2),
    margin_pct NUMERIC(5, 2),
    flip_score INTEGER,
    score_breakdown JSONB,
    llm_explanation TEXT,
    embedding vector(1536),
    status deal_status DEFAULT 'new',
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_id, external_id)
);

-- Deal Scores history table
CREATE TABLE IF NOT EXISTS deal_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    flip_score INTEGER NOT NULL,
    margin_score NUMERIC(5, 2),
    liquidity_score NUMERIC(5, 2),
    popularity_score NUMERIC(5, 2),
    size_bonus NUMERIC(5, 2),
    color_bonus NUMERIC(5, 2),
    scoring_version VARCHAR(20) DEFAULT 'v1',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vinted Stats cache table
CREATE TABLE IF NOT EXISTS vinted_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(255),
    category VARCHAR(100),
    median_price NUMERIC(10, 2),
    min_price NUMERIC(10, 2),
    max_price NUMERIC(10, 2),
    avg_price NUMERIC(10, 2),
    listing_count INTEGER DEFAULT 0,
    sold_last_7d INTEGER DEFAULT 0,
    sold_last_30d INTEGER DEFAULT 0,
    avg_days_to_sell NUMERIC(5, 1),
    price_trend NUMERIC(5, 2),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    raw_data JSONB
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    deal_id UUID REFERENCES deals(id) ON DELETE SET NULL,
    channel alert_channel NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    alert_data JSONB,
    sent_at TIMESTAMP WITH TIME ZONE,
    was_clicked BOOLEAN DEFAULT false,
    clicked_at TIMESTAMP WITH TIME ZONE,
    led_to_purchase BOOLEAN DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Outcomes table (user purchase/sale tracking)
CREATE TABLE IF NOT EXISTS outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    deal_id UUID REFERENCES deals(id) ON DELETE SET NULL,
    alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL,
    status outcome_status DEFAULT 'pending',
    purchase_price NUMERIC(10, 2),
    purchase_date DATE,
    sale_price NUMERIC(10, 2),
    sale_date DATE,
    sale_platform VARCHAR(100),
    actual_margin_amount NUMERIC(10, 2),
    actual_margin_pct NUMERIC(5, 2),
    fees_paid NUMERIC(10, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Popularity Reference table
CREATE TABLE IF NOT EXISTS popularity_reference (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(255),
    category VARCHAR(100),
    popularity_score NUMERIC(5, 2),
    search_volume INTEGER,
    trend_direction VARCHAR(20),
    data_source VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(brand, model, category)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_deals_brand ON deals(brand);
CREATE INDEX IF NOT EXISTS idx_deals_category ON deals(category);
CREATE INDEX IF NOT EXISTS idx_deals_flip_score ON deals(flip_score DESC);
CREATE INDEX IF NOT EXISTS idx_deals_margin_pct ON deals(margin_pct DESC);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_created_at ON deals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_deals_source ON deals(source_id);
CREATE INDEX IF NOT EXISTS idx_deals_available ON deals(available) WHERE available = true;

CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_deal ON alerts(deal_id);
CREATE INDEX IF NOT EXISTS idx_alerts_sent_at ON alerts(sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_outcomes_user ON outcomes(user_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_deal ON outcomes(deal_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_status ON outcomes(status);

CREATE INDEX IF NOT EXISTS idx_vinted_stats_brand ON vinted_stats(brand);
CREATE INDEX IF NOT EXISTS idx_vinted_stats_brand_model ON vinted_stats(brand, model);

-- Create vector index for similarity search (using HNSW for better performance)
CREATE INDEX IF NOT EXISTS idx_deals_embedding ON deals USING hnsw (embedding vector_cosine_ops);

-- Insert default sources
INSERT INTO sources (name, base_url, scraper_type, is_active, rate_limit_per_minute) VALUES
    ('Nike FR', 'https://www.nike.com/fr', 'nike', true, 30),
    ('Adidas FR', 'https://www.adidas.fr', 'adidas', true, 30),
    ('Zalando FR', 'https://www.zalando.fr', 'zalando', true, 60),
    ('Courir', 'https://www.courir.com', 'courir', true, 30),
    ('Foot Locker FR', 'https://www.footlocker.fr', 'footlocker', true, 30),
    ('Ralph Lauren FR', 'https://www.ralphlauren.fr', 'ralph_lauren', true, 20)
ON CONFLICT (name) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deals_updated_at BEFORE UPDATE ON deals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_outcomes_updated_at BEFORE UPDATE ON outcomes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'FlipRadar database initialized successfully!';
END $$;
