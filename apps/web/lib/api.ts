import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

// API Base URL - uses environment variable or defaults to production
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.sharkted.fr";

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Send cookies for HttpOnly auth
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  // Token is stored in localStorage for Bearer auth (API clients)
  // Cookies are sent automatically for web browsers
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth on 401
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        localStorage.removeItem("auth-storage");
        // Optionally redirect to login
        // window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH API
// ============================================================================
export const authApi = {
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),

  register: (data: { email: string; password: string; name?: string }) =>
    api.post("/auth/register", data),

  logout: () => api.post("/auth/logout"),

  me: () => api.get("/auth/me"),

  // User preferences (categories)
  getPreferences: () => api.get("/auth/me/preferences"),

  updatePreferences: (data: {
    categories?: string[];
    other_categories?: string;
  }) => api.patch("/auth/me/preferences", data),

  getCategories: () => api.get("/auth/categories"),
};

// ============================================================================
// DEALS API
// ============================================================================
export const dealsApi = {
  list: (params?: {
    page?: number;
    per_page?: number;
    brand?: string;
    category?: string;
    source?: string;
    min_score?: number;
    min_margin?: number;
    max_price?: number;
    recommended_only?: boolean;
    vinted_verified?: boolean;
    has_estimated_margin?: boolean;
    sort_by?: string;
    sort_order?: string;
    search?: string;
  }) => api.get("/v1/deals", { params }),

  get: (id: string) => api.get(`/v1/deals/${id}`),

  getTopRecommended: (limit = 10) =>
    api.get("/v1/deals", {
      params: {
        sort_by: "flip_score",
        sort_order: "desc",
        per_page: limit,
        recommended_only: true,
      },
    }),
};

// ============================================================================
// SOURCES API (was scraping)
// ============================================================================
export const scrapingApi = {
  sources: () => api.get("/v1/sources/status"),

  updateSource: (slug: string, data: { is_active?: boolean; priority?: number }) =>
    api.patch(`/v1/sources/${slug}`, data),

  run: (data?: { sources?: string[]; send_alerts?: boolean }) =>
    api.post("/v1/sources/scrape", data),

  getSettings: () => api.get("/v1/sources/settings"),

  updateSettings: (data: {
    use_rotating_proxy?: boolean;
    scrape_interval_minutes?: number;
    max_concurrent_scrapers?: number;
    min_margin_percent?: number;
    min_flip_score?: number;
  }) => api.patch("/v1/sources/settings", data),

  reloadProxies: () => api.post("/v1/sources/proxies/reload"),

  // Logs
  getLogs: (params?: { page?: number; page_size?: number }) =>
    api.get("/v1/sources/logs", { params }),

  deleteLog: (id: string) => api.delete(`/v1/sources/logs/${id}`),

  deleteLogs: (params: { older_than_days: number }) =>
    api.delete("/v1/sources/logs", { params }),

  // Rescrape Vinted stats for existing deals
  rescrapeVintedStats: (limit: number = 100) =>
    api.post("/v1/sources/rescrape-vinted-stats", null, { params: { limit } }),
};

// ============================================================================
// ANALYTICS API
// ============================================================================
export const analyticsApi = {
  dashboard: () => api.get("/v1/deals/stats"),

  brands: (limit?: number) => api.get("/v1/deals/stats/brands", { params: { limit } }),

  categories: () => api.get("/v1/deals/stats/categories"),

  trends: (params?: { days?: number }) =>
    api.get("/v1/deals/stats/trends", { params }),

  dealsTrend: (days?: number) => api.get("/v1/deals/stats/trends", { params: { days } }),

  scoreDistribution: () => api.get("/v1/deals/stats/score-distribution"),

  sourcePerformance: () => api.get("/v1/deals/stats/sources"),
};

// ============================================================================
// ALERTS API
// ============================================================================
export const alertsApi = {
  list: (params?: { page?: number; per_page?: number; unread_only?: boolean }) =>
    api.get("/v1/alerts", { params }),

  markRead: (id: string) => api.patch(`/v1/alerts/${id}/read`),

  markAllRead: () => api.patch("/v1/alerts/read-all"),

  getUnreadCount: () => api.get("/v1/alerts/unread-count"),

  stats: (days?: number) => api.get("/v1/alerts/stats", { params: { days } }),
};

// ============================================================================
// OUTCOMES API (tracking purchases)
// ============================================================================
export const outcomesApi = {
  list: (params?: { page?: number; per_page?: number }) =>
    api.get("/v1/outcomes", { params }),

  create: (data: {
    deal_id: string;
    action: "bought" | "ignored" | "watched";
    buy_price?: number;
    buy_size?: string;
  }) => api.post("/v1/outcomes", data),

  update: (id: string, data: {
    sold?: boolean;
    sell_price?: number;
    sell_date?: string;
    sell_platform?: string;
    notes?: string;
  }) => api.patch(`/v1/outcomes/${id}`, data),

  delete: (id: string) => api.delete(`/v1/outcomes/${id}`),
};

// ============================================================================
// ADMIN API
// ============================================================================
export const adminApi = {
  stats: () => api.get("/v1/admin/stats"),

  // Users
  users: () => api.get("/v1/admin/users"),
  updateUserPlan: (userId: number, plan: string) => api.patch(`/v1/admin/users/${userId}/plan`, { plan }),
  deleteUser: (userId: number) => api.delete(`/v1/admin/users/${userId}`),

  // Subscription tiers
  subscriptionTiers: () => api.get("/v1/admin/subscription-tiers"),

  // Proxies
  proxies: () => api.get("/v1/admin/proxies"),
  createProxy: (data: {
    name: string;
    provider: string;
    proxy_type: string;
    host: string;
    port: number;
    username: string;
    password: string;
    country?: string;
    zone?: string;
    enabled?: boolean;
    is_default?: boolean;
  }) => api.post("/v1/admin/proxies", data),
  getProxy: (id: number) => api.get(`/v1/admin/proxies/${id}`),
  updateProxy: (id: number, data: Record<string, unknown>) => api.patch(`/v1/admin/proxies/${id}`, data),
  deleteProxy: (id: number) => api.delete(`/v1/admin/proxies/${id}`),
  testProxy: (id: number) => api.post(`/v1/admin/proxies/${id}/test`),

  // Proxy costs
  proxyCosts: (days?: number) => api.get("/v1/admin/proxy-costs", { params: { days } }),
  proxyDecisionTest: (site: string, score?: number, hasAlert?: boolean) =>
    api.get("/v1/admin/proxy-decision-test", { params: { site, score, has_alert: hasAlert } }),

  // Scraping Health Check & Auto-repair
  scrapingHealth: () => api.get("/v1/admin/scraping/health"),
  scrapingFailures: () => api.get("/v1/admin/scraping/failures"),
  diagnoseSource: (source: string) => api.post(`/v1/admin/scraping/diagnose/${source}`),
  repairAllSources: () => api.post("/v1/admin/scraping/repair-all"),
};


// ============================================================================
// FAVORITES API
// ============================================================================
export const favoritesApi = {
  list: (userId: string | number, params?: { page?: number; per_page?: number }) =>
    api.get("/v1/favorites", { params: { user_id: userId, ...params } }),

  add: (userId: string | number, dealId: string | number, notes?: string) =>
    api.post(`/v1/favorites?user_id=${userId}`, { deal_id: dealId, notes }),

  remove: (userId: string | number, dealId: string | number) =>
    api.delete(`/v1/favorites/${dealId}?user_id=${userId}`),

  check: (userId: string | number, dealId: string | number) =>
    api.get(`/v1/favorites/check/${dealId}?user_id=${userId}`),

  getIds: (userId: string | number) =>
    api.get(`/v1/favorites/ids?user_id=${userId}`),
};

// ============================================================================
// USER API
// ============================================================================
export const userApi = {
  getProfile: () => api.get("/v1/users/me"),

  updateProfile: (data: {
    name?: string;
    discord_webhook?: string;
    email_alerts?: boolean;
    alert_threshold?: number;
  }) => api.patch("/v1/users/me", data),

  updatePreferences: (data: {
    min_margin?: number;
    categories?: string[];
    sizes?: string[];
    brands?: string[];
    risk_profile?: "conservative" | "balanced" | "aggressive";
  }) => api.patch("/v1/users/me/preferences", data),
};

export default api;
