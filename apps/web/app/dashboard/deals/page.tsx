"use client";

import { useState } from "react";
import { LayoutGrid, List, ChevronLeft, ChevronRight } from "lucide-react";
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

  return (
    <div>
      <Header
        title="Deals"
        subtitle={`${data?.total || 0} deals trouvés`}
      />

      <div className="p-4 sm:p-6 lg:p-8">
        {/* Filters */}
        <div className="mb-4 sm:mb-6">
          <DealFilters onFiltersChange={handleFiltersChange} />
        </div>

        {/* View Toggle & Page Info */}
        <div className="flex items-center justify-between mb-4 gap-2">
          <p className="text-xs sm:text-sm text-gray-500">
            Page {page}/{data?.pages || 1}
          </p>
          {/* View toggle - Hidden on mobile (always grid), visible on tablet+ */}
          <div className="hidden sm:flex items-center gap-1 bg-gray-100 p-1 rounded-lg">
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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="h-72 sm:h-80 bg-gray-100 rounded-xl animate-pulse"
              />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 sm:py-12 text-red-500">
            Erreur lors du chargement des deals
          </div>
        ) : ((data?.items || data?.deals || []).length === 0) ? (
          <div className="text-center py-8 sm:py-12 text-gray-500">
            Aucun deal trouvé avec ces filtres
          </div>
        ) : viewMode === "grid" || (typeof window !== "undefined" && window.innerWidth < 640) ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
            {(data?.items || data?.deals || []).map((deal: any) => (
              <DealCard key={deal.id} deal={deal} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
            <DealTable deals={data?.items || data?.deals || []} />
          </div>
        )}

        {/* Pagination */}
        {data && (data.pages || 1) > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6 sm:mt-8">
            {/* Mobile: Simple prev/next with icons */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="sm:hidden"
              aria-label="Page précédente"
            >
              <ChevronLeft size={18} />
            </Button>

            {/* Mobile: Page indicator */}
            <span className="sm:hidden text-sm font-medium text-gray-700 px-3">
              {page} / {data.pages || 1}
            </span>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(data.pages || 1, p + 1))}
              disabled={page === (data.pages || 1)}
              className="sm:hidden"
              aria-label="Page suivante"
            >
              <ChevronRight size={18} />
            </Button>

            {/* Desktop: Full pagination */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="hidden sm:flex"
            >
              Précédent
            </Button>
            <div className="hidden sm:flex items-center gap-1">
              {Array.from({ length: Math.min(5, data.pages || 1) }, (_, i) => {
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
              {(data.pages || 1) > 5 && <span className="px-2">...</span>}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(data.pages || 1, p + 1))}
              disabled={page === (data.pages || 1)}
              className="hidden sm:flex"
            >
              Suivant
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
