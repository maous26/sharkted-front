"use client";

import Link from "next/link";
import Image from "next/image";
import { ExternalLink, ChevronUp, ChevronDown, Minus, Heart, Clock } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { SourceBadge, TimeIndicator } from "@/components/ui/indicators";
import { Deal } from "@/types";
import { formatPrice, cn, proxyImageUrl } from "@/lib/utils";
import { useFavoriteIds, useToggleFavorite } from "@/hooks/use-favorites";
import { useAuth } from "@/hooks/use-auth";

interface DealTableProps {
  deals: Deal[];
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  onSort?: (column: string) => void;
}

// Sortable header component
function SortableHeader({
  children,
  column,
  currentSort,
  sortOrder,
  onSort,
}: {
  children: React.ReactNode;
  column: string;
  currentSort?: string;
  sortOrder?: "asc" | "desc";
  onSort?: (column: string) => void;
}) {
  const isActive = currentSort === column;

  return (
    <button
      onClick={() => onSort?.(column)}
      className={cn(
        "flex items-center gap-1 font-semibold hover:text-blue-600 transition-colors",
        isActive && "text-blue-600"
      )}
    >
      {children}
      {isActive ? (
        sortOrder === "asc" ? (
          <ChevronUp size={14} />
        ) : (
          <ChevronDown size={14} />
        )
      ) : (
        <Minus size={14} className="opacity-0 group-hover:opacity-50" />
      )}
    </button>
  );
}

export function DealTable({ deals, sortBy, sortOrder, onSort }: DealTableProps) {
  const { isAuthenticated } = useAuth();
  const { data: favoriteIds = [] } = useFavoriteIds();
  const { toggleFavorite, isLoading: isFavoriteLoading } = useToggleFavorite();

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="bg-gray-50 hover:bg-gray-50">
            <TableHead className="w-[350px]">
              <SortableHeader
                column="product_name"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Produit
              </SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader
                column="price"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Prix
              </SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader
                column="discount"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Décote
              </SortableHeader>
            </TableHead>
            <TableHead>Tailles</TableHead>
            <TableHead>
              <SortableHeader
                column="detected_at"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Détecté
              </SortableHeader>
            </TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {deals.map((deal, index) => {
            const dealIdNum = parseInt(deal.id, 10);
            const isFavorite = favoriteIds.includes(dealIdNum);
            const isRecent = index < 3;
            const discountPct = deal.discount_pct || 0;
            const isGreatDeal = discountPct >= 50;
            const isGoodDeal = discountPct >= 30 && discountPct < 50;

            return (
              <TableRow
                key={deal.id}
                className={cn(
                  "group transition-colors",
                  isRecent && "bg-blue-50/30",
                  isGreatDeal && "bg-green-50/40",
                  "hover:bg-gray-50"
                )}
              >
                {/* Product */}
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="w-16 h-16 relative rounded-lg overflow-hidden bg-gray-100 flex-shrink-0 ring-1 ring-gray-200">
                      {deal.image_url ? (
                        <Image
                          src={proxyImageUrl(deal.image_url)}
                          alt={deal.product_name}
                          fill
                          unoptimized
                          className="object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">
                          N/A
                        </div>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {deal.source_name && (
                          <SourceBadge source={deal.source_name} size="sm" />
                        )}
                        <span className="text-xs text-blue-600 font-semibold uppercase">
                          {deal.brand}
                        </span>
                      </div>
                      <p className="font-semibold text-gray-900 truncate max-w-[250px] leading-tight">
                        {deal.product_name}
                      </p>
                    </div>
                  </div>
                </TableCell>

                {/* Price */}
                <TableCell>
                  <div>
                    <p className="text-lg font-bold text-gray-900">
                      {formatPrice(deal.sale_price)}
                    </p>
                    {deal.original_price && deal.original_price > deal.sale_price && (
                      <span className="text-sm text-gray-400 line-through">
                        {formatPrice(deal.original_price)}
                      </span>
                    )}
                  </div>
                </TableCell>

                {/* Discount */}
                <TableCell>
                  {discountPct > 0 ? (
                    <span className={cn(
                      "inline-flex items-center px-3 py-1.5 rounded-lg font-bold text-sm",
                      isGreatDeal && "bg-green-500 text-white",
                      isGoodDeal && "bg-yellow-400 text-yellow-900",
                      !isGreatDeal && !isGoodDeal && "bg-gray-100 text-gray-700"
                    )}>
                      -{discountPct.toFixed(0)}%
                    </span>
                  ) : (
                    <span className="text-gray-400 text-sm">—</span>
                  )}
                </TableCell>

                {/* Sizes */}
                <TableCell>
                  {deal.sizes_available && deal.sizes_available.length > 0 ? (
                    <div className="flex flex-wrap gap-1 max-w-[120px]">
                      {deal.sizes_available.slice(0, 4).map((size, idx) => (
                        <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                          {size}
                        </span>
                      ))}
                      {deal.sizes_available.length > 4 && (
                        <span className="text-xs text-gray-400">+{deal.sizes_available.length - 4}</span>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-400 text-sm">—</span>
                  )}
                </TableCell>

                {/* Time */}
                <TableCell>
                  <div className="flex items-center gap-1.5 text-gray-500">
                    <Clock size={14} />
                    <TimeIndicator date={deal.detected_at} size="sm" />
                  </div>
                </TableCell>

                {/* Actions */}
                <TableCell>
                  <div className="flex items-center justify-end gap-2">
                    {isAuthenticated && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className={cn(
                          "transition-colors",
                          isFavorite 
                            ? "text-red-500 bg-red-50 hover:bg-red-100" 
                            : "text-gray-400 hover:text-red-500 hover:bg-red-50"
                        )}
                        onClick={() => toggleFavorite(dealIdNum)}
                        disabled={isFavoriteLoading}
                      >
                        <Heart size={16} fill={isFavorite ? "currentColor" : "none"} />
                      </Button>
                    )}
                    <Link href={deal.product_url} target="_blank">
                      <Button 
                        variant="primary" 
                        size="sm" 
                        className={cn(
                          "font-medium",
                          isGreatDeal ? "bg-green-600 hover:bg-green-700" : "bg-blue-600 hover:bg-blue-700"
                        )}
                      >
                        <ExternalLink size={14} className="mr-1" />
                        Voir
                      </Button>
                    </Link>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
