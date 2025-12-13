"use client";

import { useState } from "react";
import { LayoutGrid, List } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { DealCard } from "@/components/deals/deal-card";
import { DealTable } from "@/components/deals/deal-table";
import { DealFilters } from "@/components/deals/deal-filters";
import { useDeals } from "@/hooks/use-deals";
import { cn } from "@/lib/utils";

export default function DealsPage() {
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, any>>({
    sort_by: "detected_at",
    sort_order: "desc",
  });

  const { data, isLoading, error } = useDeals({
    page,
    per_page: viewMode === "grid" ? 12 : 20,
    ...filters,
  });

  const handleFiltersChange = (newFilters: Record<string, any>) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleTrackDeal = (deal: any) => {
    // TODO: Open track modal
    console.log("Track deal:", deal);
  };

  return (
    <div>
      <Header
        title="Deals"
        subtitle={`${data?.total || 0} deals trouvés`}
      />

      <div className="p-8">
        {/* Filters */}
        <div className="mb-6">
          <DealFilters onFiltersChange={handleFiltersChange} />
        </div>

        {/* View Toggle */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-gray-500">
            Page {page} sur {data?.pages || 1}
          </p>
          <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg">
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "px-3",
                viewMode === "grid" && "bg-white shadow-sm"
              )}
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid size={18} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "px-3",
                viewMode === "table" && "bg-white shadow-sm"
              )}
              onClick={() => setViewMode("table")}
            >
              <List size={18} />
            </Button>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="h-80 bg-gray-100 rounded-xl animate-pulse"
              />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-500">
            Erreur lors du chargement des deals
          </div>
        ) : data?.items.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            Aucun deal trouvé avec ces filtres
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {data?.items.map((deal) => (
              <DealCard key={deal.id} deal={deal} onTrack={handleTrackDeal} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <DealTable deals={data?.items || []} onTrack={handleTrackDeal} />
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Précédent
            </Button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, data.pages) }, (_, i) => {
                const pageNum = i + 1;
                return (
                  <Button
                    key={pageNum}
                    variant={page === pageNum ? "primary" : "ghost"}
                    size="sm"
                    onClick={() => setPage(pageNum)}
                  >
                    {pageNum}
                  </Button>
                );
              })}
              {data.pages > 5 && <span className="px-2">...</span>}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page === data.pages}
            >
              Suivant
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
