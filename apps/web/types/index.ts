export interface User {
  id: string;
  email: string;
  username?: string;
  full_name?: string;
  plan: string;
  preferences?: UserPreferences;
  discord_webhook?: string;
  email_alerts: boolean;
  alert_threshold: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface UserPreferences {
  min_margin?: number;
  categories?: string[];
  sizes?: string[];
  brands?: string[];
  risk_profile?: "conservative" | "balanced" | "aggressive";
}

export interface VintedStats {
  nb_listings: number;
  price_min?: number;
  price_max?: number;
  price_median?: number;
  margin_euro?: number;
  margin_pct?: number;
  liquidity_score?: number;
}

export interface DealScore {
  flip_score: number;
  recommended_action?: "buy" | "watch" | "ignore";
  recommended_price?: number;
  confidence?: number;
  explanation_short?: string;
  risks?: string[];
  estimated_sell_days?: number;
}

export interface Deal {
  id: string;
  product_name: string;
  brand?: string;
  model?: string;
  category?: string;
  color?: string;
  gender?: string;
  original_price?: number;
  sale_price: number;
  discount_pct?: number;
  product_url: string;
  image_url?: string;
  sizes_available?: string[];
  stock_available: boolean;
  source_name?: string;
  detected_at: string;
  vinted_stats?: VintedStats;
  score?: DealScore;
}

export interface DealsListResponse {
  items?: Deal[];
  deals?: Deal[];  // API returns 'deals' instead of 'items'
  total: number;
  page?: number;
  per_page?: number;
  pages?: number;
  limit?: number;
  offset?: number;
  has_more?: boolean;
}

export interface Outcome {
  id: string;
  deal_id: string;
  action: "bought" | "ignored" | "watched";
  buy_price?: number;
  buy_date?: string;
  buy_size?: string;
  sold: boolean;
  sell_price?: number;
  sell_date?: string;
  sell_platform?: string;
  actual_margin_euro?: number;
  actual_margin_pct?: number;
  days_to_sell?: number;
  was_good_deal?: boolean;
  notes?: string;
  created_at: string;
}

export interface Alert {
  id: string;
  deal_id: string;
  channel: string;
  status: string;
  alert_data?: Record<string, any>;
  was_clicked: boolean;
  led_to_purchase: boolean;
  sent_at: string;
}

export interface DashboardStats {
  total_deals: number;
  deals_today: number;
  avg_flip_score: number;
  top_deals_count: number;
  total_sources: number;
  last_scan?: string;
}

export interface BrandStats {
  brand: string;
  deal_count: number;
  avg_flip_score: number;
  avg_margin_pct: number;
  avg_liquidity: number;
}

export interface CategoryStats {
  category: string;
  deal_count: number;
  avg_flip_score: number;
  avg_margin_pct: number;
}
