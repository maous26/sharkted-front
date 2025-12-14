"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dealsApi, outcomesApi } from "@/lib/api";
import { Deal, DealsListResponse } from "@/types";

interface DealsQueryParams {
  page?: number;
  per_page?: number;
  brand?: string;
  category?: string;
  source?: string;
  min_score?: number;
  min_margin?: number;
  max_price?: number;
  recommended_only?: boolean;
  sort_by?: string;
  sort_order?: string;
}

// Map API response to frontend Deal format
function mapApiDealToFrontend(apiDeal: any): Deal {
  return {
    id: String(apiDeal.id),
    product_name: apiDeal.title || apiDeal.product_name || "Unknown",
    brand: apiDeal.seller_name || apiDeal.brand || apiDeal.source || "",
    model: apiDeal.model || "",
    category: apiDeal.category || "",
    color: apiDeal.color || "",
    gender: apiDeal.gender || "",
    original_price: apiDeal.original_price || undefined,
    sale_price: apiDeal.price || apiDeal.sale_price || 0,
    discount_pct: apiDeal.discount_percent || apiDeal.discount_pct || undefined,
    product_url: apiDeal.url || apiDeal.product_url || "",
    image_url: apiDeal.image_url || undefined,
    sizes_available: apiDeal.sizes_available || [],
    stock_available: apiDeal.in_stock ?? true,
    source_name: apiDeal.source || apiDeal.source_name || "",
    detected_at: apiDeal.first_seen_at || apiDeal.detected_at || new Date().toISOString(),
    vinted_stats: apiDeal.vinted_stats || undefined,
    score: apiDeal.score || undefined,
  };
}

function mapApiResponseToFrontend(data: any): DealsListResponse {
  const deals = (data.deals || data.items || []).map(mapApiDealToFrontend);
  return {
    items: deals,
    deals: deals,
    total: data.total || 0,
    page: data.page || 1,
    per_page: data.per_page || data.limit || 20,
    pages: data.pages || Math.ceil((data.total || 0) / (data.per_page || data.limit || 20)) || 1,
    limit: data.limit,
    offset: data.offset,
    has_more: data.has_more,
  };
}

export function useDeals(params: DealsQueryParams = {}) {
  return useQuery<DealsListResponse>({
    queryKey: ["deals", params],
    queryFn: async () => {
      const { data } = await dealsApi.list(params);
      return mapApiResponseToFrontend(data);
    },
  });
}

export function useDeal(id: string) {
  return useQuery<Deal>({
    queryKey: ["deal", id],
    queryFn: async () => {
      const { data } = await dealsApi.get(id);
      return mapApiDealToFrontend(data);
    },
    enabled: !!id,
  });
}

export function useTopDeals(limit = 10) {
  return useQuery<Deal[]>({
    queryKey: ["deals", "top", limit],
    queryFn: async () => {
      const { data } = await dealsApi.getTopRecommended(limit);
      // API returns { deals: [...] } or array directly
      const deals = Array.isArray(data) ? data : (data.deals || data.items || []);
      return deals.map(mapApiDealToFrontend);
    },
  });
}

export function useTrackDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      deal_id: string;
      action: "bought" | "ignored" | "watched";
      buy_price?: number;
      buy_size?: string;
    }) => {
      const response = await outcomesApi.create(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outcomes"] });
    },
  });
}
