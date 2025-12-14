"use client";

import Link from "next/link";
import Image from "next/image";
import { ExternalLink, Eye, ChevronUp, ChevronDown, Minus } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  FlipScoreCircle,
  ProfitIndicator,
  ActionBadge,
  TimeIndicator,
  SourceBadge,
  LiquidityIndicator,
} from "@/components/ui/indicators";
import { Deal } from "@/types";
import { formatPrice, cn } from "@/lib/utils";

interface DealTableProps {
  deals: Deal[];
  onTrack?: (deal: Deal) => void;
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
        "flex items-center gap-1 font-semibold hover:text-primary-600 transition-colors",
        isActive && "text-primary-600"
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

export function DealTable({ deals, onTrack, sortBy, sortOrder, onSort }: DealTableProps) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="bg-gray-50 hover:bg-gray-50">
            <TableHead className="w-[300px]">
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
                column="sale_price"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Prix
              </SortableHeader>
            </TableHead>
            <TableHead>Vinted</TableHead>
            <TableHead>
              <SortableHeader
                column="margin_pct"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Profit
              </SortableHeader>
            </TableHead>
            <TableHead>
              <SortableHeader
                column="flip_score"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Score
              </SortableHeader>
            </TableHead>
            <TableHead>Liquidite</TableHead>
            <TableHead>
              <SortableHeader
                column="detected_at"
                currentSort={sortBy}
                sortOrder={sortOrder}
                onSort={onSort}
              >
                Detecte
              </SortableHeader>
            </TableHead>
            <TableHead>Reco</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {deals.map((deal, index) => {
            const isNew = index < 2; // First 2 deals considered "new"
            const hasStats = deal.vinted_stats && deal.vinted_stats.nb_listings > 0;

            return (
              <TableRow
                key={deal.id}
                className={cn(
                  "group transition-colors",
                  isNew && "bg-green-50/50",
                  "hover:bg-gray-50"
                )}
              >
                {/* Product */}
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="w-14 h-14 relative rounded-lg overflow-hidden bg-gray-100 flex-shrink-0 ring-1 ring-gray-200">
                      {deal.image_url ? (
                        <Image
                          src={deal.image_url}
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
                      {isNew && (
                        <div className="absolute top-0 right-0 w-2 h-2 bg-green-500 rounded-full" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        {deal.source_name && (
                          <SourceBadge source={deal.source_name} size="sm" />
                        )}
                      </div>
                      <p className="font-semibold text-gray-900 truncate max-w-[200px] leading-tight">
                        {deal.product_name}
                      </p>
                      <p className="text-sm text-gray-500">{deal.brand}</p>
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
                      <div className="flex items-center gap-1">
                        <span className="text-sm text-gray-400 line-through">
                          {formatPrice(deal.original_price)}
                        </span>
                        <span className="text-xs font-bold text-red-500">
                          -{deal.discount_pct?.toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </TableCell>

                {/* Vinted */}
                <TableCell>
                  {hasStats ? (
                    <div>
                      <p className="font-semibold text-gray-900">
                        {formatPrice(deal.vinted_stats!.price_median || 0)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {deal.vinted_stats!.nb_listings} annonces
                      </p>
                    </div>
                  ) : (
                    <span className="text-gray-400 text-sm">Non analyse</span>
                  )}
                </TableCell>

                {/* Profit */}
                <TableCell>
                  {hasStats && deal.vinted_stats!.margin_pct ? (
                    <ProfitIndicator
                      marginEuro={deal.vinted_stats!.margin_euro}
                      marginPct={deal.vinted_stats!.margin_pct}
                      size="md"
                    />
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </TableCell>

                {/* Score */}
                <TableCell>
                  {deal.score ? (
                    <FlipScoreCircle
                      score={deal.score.flip_score}
                      size="sm"
                      showLabel={false}
                    />
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </TableCell>

                {/* Liquidity */}
                <TableCell>
                  {hasStats ? (
                    <LiquidityIndicator
                      score={deal.vinted_stats!.liquidity_score || 50}
                      size="sm"
                    />
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </TableCell>

                {/* Time */}
                <TableCell>
                  <TimeIndicator date={deal.detected_at} size="sm" />
                </TableCell>

                {/* Recommendation */}
                <TableCell>
                  {deal.score?.recommended_action ? (
                    <ActionBadge
                      action={deal.score.recommended_action}
                      size="sm"
                      animated={deal.score.recommended_action === "buy"}
                    />
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </TableCell>

                {/* Actions */}
                <TableCell>
                  <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => onTrack?.(deal)}
                      className="bg-primary-600 hover:bg-primary-700"
                    >
                      <Eye size={14} className="mr-1" />
                      Tracker
                    </Button>
                    <Link href={deal.product_url} target="_blank">
                      <Button variant="outline" size="sm">
                        <ExternalLink size={14} />
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
