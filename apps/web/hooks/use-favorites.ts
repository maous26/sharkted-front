"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { favoritesApi } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

interface Favorite {
  id: number;
  user_id: number;
  deal_id: number;
  notes?: string;
  created_at: string;
  deal?: any;
}

interface FavoritesResponse {
  favorites: Favorite[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export function useFavorites(params?: { page?: number; per_page?: number }) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery<FavoritesResponse>({
    queryKey: ["favorites", userId, params],
    queryFn: async () => {
      if (!userId) throw new Error("User not authenticated");
      const { data } = await favoritesApi.list(userId, params);
      return data;
    },
    enabled: !!userId,
  });
}

export function useFavoriteIds() {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery<number[]>({
    queryKey: ["favoriteIds", userId],
    queryFn: async () => {
      if (!userId) return [];
      const { data } = await favoritesApi.getIds(userId);
      return data.deal_ids || [];
    },
    enabled: !!userId,
  });
}

export function useIsFavorite(dealId: number) {
  const { data: favoriteIds = [] } = useFavoriteIds();
  return favoriteIds.includes(dealId);
}

export function useAddFavorite() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: async ({ dealId, notes }: { dealId: number; notes?: string }) => {
      if (!userId) throw new Error("User not authenticated");
      const { data } = await favoritesApi.add(userId, dealId, notes);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
      queryClient.invalidateQueries({ queryKey: ["favoriteIds"] });
    },
  });
}

export function useRemoveFavorite() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: async (dealId: number) => {
      if (!userId) throw new Error("User not authenticated");
      const { data } = await favoritesApi.remove(userId, dealId);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
      queryClient.invalidateQueries({ queryKey: ["favoriteIds"] });
    },
  });
}

export function useToggleFavorite() {
  const addFavorite = useAddFavorite();
  const removeFavorite = useRemoveFavorite();
  const { data: favoriteIds = [] } = useFavoriteIds();

  const toggleFavorite = async (dealId: number) => {
    const isFavorite = favoriteIds.includes(dealId);
    if (isFavorite) {
      await removeFavorite.mutateAsync(dealId);
    } else {
      await addFavorite.mutateAsync({ dealId });
    }
  };

  return {
    toggleFavorite,
    isLoading: addFavorite.isPending || removeFavorite.isPending,
  };
}
