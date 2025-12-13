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

export function useDeals(params: DealsQueryParams = {}) {
  return useQuery<DealsListResponse>({
    queryKey: ["deals", params],
    queryFn: async () => {
      const { data } = await dealsApi.list(params);
      return data;
    },
  });
}

export function useDeal(id: string) {
  return useQuery<Deal>({
    queryKey: ["deal", id],
    queryFn: async () => {
      const { data } = await dealsApi.get(id);
      return data;
    },
    enabled: !!id,
  });
}

export function useTopDeals(limit = 10) {
  return useQuery<Deal[]>({
    queryKey: ["deals", "top", limit],
    queryFn: async () => {
      const { data } = await dealsApi.getTopRecommended(limit);
      return data;
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
