"use client";

import { useState } from "react";
import { Heart, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { DealCard } from "@/components/deals/deal-card";
import { useFavorites, useRemoveFavorite } from "@/hooks/use-favorites";
import { useAuth } from "@/hooks/use-auth";
import { Deal } from "@/types";

// Map favorite deal data to frontend Deal format
function mapFavoriteToDeal(favorite: any): Deal {
  const deal = favorite.deal || {};
  return {
    id: String(deal.id || favorite.deal_id),
    product_name: deal.title || deal.product_name || "Unknown",
    brand: deal.seller_name || deal.brand || deal.source || "",
    model: deal.model || "",
    category: deal.category || "",
    color: deal.color || "",
    gender: deal.gender || "",
    original_price: deal.original_price || undefined,
    sale_price: deal.price || deal.sale_price || 0,
    discount_pct: deal.discount_percent || deal.discount_pct || undefined,
    product_url: deal.url || deal.product_url || "",
    image_url: deal.image_url || undefined,
    sizes_available: deal.sizes_available || [],
    stock_available: deal.in_stock ?? true,
    source_name: deal.source || deal.source_name || "",
    detected_at: deal.first_seen_at || deal.detected_at || new Date().toISOString(),
    vinted_stats: deal.vinted_stats || undefined,
    score: deal.score || undefined,
  };
}

export default function FavoritesPage() {
  const [page, setPage] = useState(1);
  const { isAuthenticated, hasHydrated } = useAuth();
  const { data, isLoading, error } = useFavorites({ page, per_page: 12 });
  const removeFavorite = useRemoveFavorite();

  // Wait for hydration
  if (!hasHydrated) {
    return (
      <div>
        <Header title="Favoris" subtitle="Chargement..." />
        <div className="p-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-80 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <div>
        <Header title="Favoris" subtitle="Connectez-vous pour voir vos favoris" />
        <div className="p-8">
          <div className="text-center py-12">
            <Heart className="mx-auto h-16 w-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Connectez-vous pour voir vos favoris
            </h3>
            <p className="text-gray-500">
              Créez un compte ou connectez-vous pour sauvegarder vos deals préférés.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const favorites = data?.favorites || [];
  const totalPages = data?.pages || 1;

  return (
    <div>
      <Header
        title="Favoris"
        subtitle={`${data?.total || 0} deals sauvegardés`}
      />

      <div className="p-4 sm:p-6 lg:p-8">
        {/* Page Info */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">
              Page {page}/{totalPages}
            </p>
          </div>
        )}

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-80 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-500">
            Erreur lors du chargement des favoris
          </div>
        ) : favorites.length === 0 ? (
          <div className="text-center py-12">
            <Heart className="mx-auto h-16 w-16 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Aucun favori
            </h3>
            <p className="text-gray-500">
              Cliquez sur le coeur sur un deal pour le sauvegarder ici.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {favorites.map((favorite: any) => (
              <DealCard key={favorite.id} deal={mapFavoriteToDeal(favorite)} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft size={18} className="mr-1" />
              Précédent
            </Button>
            <span className="text-sm text-gray-500 px-4">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Suivant
              <ChevronRight size={18} className="ml-1" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
