"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ExternalLink, Eye, Zap, CheckCircle, RefreshCw } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  SharkScoreCircle,
  ProfitIndicator,
  TimeIndicator,
  ActionBadge,
  SourceBadge,
} from "@/components/ui/indicators";

import { formatPrice, cn, proxyImageUrl } from "@/lib/utils";
import { useFavoriteIds, useToggleFavorite } from "@/hooks/use-favorites";
import { useAuth } from "@/hooks/use-auth";
import { Deal } from "../../types";

export interface DealCardProps {
  deal: Deal;
  isNew?: boolean;
  compact?: boolean;
}

export function DealCard({ deal, isNew = false }: DealCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isRescoring, setIsRescoring] = useState(false);
  const { isAuthenticated, user } = useAuth();
  const { data: favoriteIds = [] } = useFavoriteIds();
  const { toggleFavorite, isLoading: isFavoriteLoading } = useToggleFavorite();

  const dealIdNum = parseInt(deal.id, 10);
  const isFavorite = favoriteIds.includes(dealIdNum);
  const hasScore = deal.score && deal.score.flip_score > 0;
  const isAdmin = user?.plan === "admin";

  const handleRescore = async () => {
    if (isRescoring) return;
    setIsRescoring(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/scoring/score/${dealIdNum}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      if (response.ok) {
        // Refresh the page to see updated data
        window.location.reload();
      }
    } catch (error) {
      console.error("Rescore error:", error);
    } finally {
      setIsRescoring(false);
    }
  };

  // Couleur de bordure selon la recommandation
  const borderColor = deal.score?.recommended_action === "buy"
    ? "ring-2 ring-green-500"
    : deal.score?.recommended_action === "watch"
      ? "ring-2 ring-yellow-400"
      : "";

  return (
    <Card
      className={cn(
        "overflow-hidden transition-all duration-300 group relative",
        isHovered ? "shadow-xl scale-[1.02]" : "hover:shadow-lg",
        isNew && "ring-2 ring-green-500 ring-opacity-50",
        !isNew && borderColor
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Badge NOUVEAU pour items frais */}
      {isNew && (
        <div className="absolute top-0 left-0 z-20 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-br-lg flex items-center gap-1">
          <Zap size={12} />
          NOUVEAU
        </div>
      )}

      {/* Badge BUY en haut si recommandé */}
      {deal.score?.recommended_action === "buy" && !isNew && (
        <div className="absolute top-0 left-0 z-20 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xs font-bold px-3 py-1 rounded-br-lg flex items-center gap-1 animate-pulse">
          <CheckCircle size={12} />
          ACHETER
        </div>
      )}

      {/* Image Container */}
      <div className="relative h-48 bg-gray-100 overflow-hidden">
        {deal.image_url ? (
          <Image
            src={proxyImageUrl(deal.image_url)}
            alt={deal.product_name}
            fill
            unoptimized
            className={cn(
              "object-cover transition-transform duration-300",
              isHovered && "scale-110"
            )}
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            Pas d image
          </div>
        )}

        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

        {/* SharkScore Badge - Top Left */}
        {hasScore && !isNew && deal.score?.recommended_action !== "buy" && (
          <div className="absolute top-3 left-3 z-10">
            <div className="bg-white/95 backdrop-blur rounded-xl p-2 shadow-lg flex flex-col items-center gap-1">
              <SharkScoreCircle score={deal.score!.flip_score} size="sm" showLabel={false} />
              {/* Petit badge Vérifié si Vinted Data */}
              {deal.vinted_stats && (
                <span className="text-[8px] bg-green-100 text-green-700 px-1 rounded font-bold uppercase tracking-tighter">
                  Vérifié
                </span>
              )}
            </div>
          </div>
        )}

        {/* Source Badge - Top Right */}
        {deal.source_name && (
          <div className="absolute top-3 right-3 z-10">
            <SourceBadge source={deal.source_name} size="sm" />
          </div>
        )}

        {/* Time Indicator - Bottom Left */}
        <div className="absolute bottom-3 left-3 z-10">
          <div className="bg-black/70 backdrop-blur rounded-lg px-2 py-1">
            <TimeIndicator date={deal.detected_at} size="sm" showExactDate />
          </div>
        </div>

        {/* Quick Action - Bottom Right (visible on hover) */}
        <div
          className={cn(
            "absolute bottom-3 right-3 z-10 transition-all duration-200",
            isHovered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
          )}
        >
          <Link href={deal.product_url} target="_blank">
            <Button
              variant="ghost"
              size="sm"
              className="bg-white/90 text-gray-900 hover:bg-white shadow-lg h-9 w-9 p-0"
            >
              <ExternalLink size={16} />
            </Button>
          </Link>
        </div>
      </div>

      <CardContent className="p-4">
        {/* Brand & Name */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold text-primary-600 uppercase tracking-wider">
              {deal.brand}
            </p>
            {deal.score?.recommended_action && (
              <ActionBadge
                action={deal.score.recommended_action}
                size="sm"
                animated={deal.score.recommended_action === "buy"}
              />
            )}
          </div>
          <h3 className="font-bold text-gray-900 line-clamp-2 leading-tight">
            {deal.product_name}
          </h3>
        </div>

        {/* Prix avec remise */}
        <div className="flex items-baseline gap-2 mb-4">
          <span className="text-2xl font-bold text-gray-900">
            {formatPrice(deal.sale_price)}
          </span>
          {deal.original_price && deal.original_price > deal.sale_price && (
            <span className="text-sm text-gray-400 line-through">
              {formatPrice(deal.original_price)}
            </span>
          )}
          {deal.discount_pct && deal.discount_pct > 0 && (
            <span className="text-sm font-bold text-red-500">
              -{deal.discount_pct.toFixed(0)}%
            </span>
          )}
        </div>

        {/* Bloc Scoring Simplifié - Toutes les infos importantes */}
        {hasScore && (
          <div className="bg-gradient-to-br from-gray-50 to-blue-50/30 rounded-xl p-3 mb-4 border border-gray-100">
            {/* SharkScore + Marge principale */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <SharkScoreCircle score={deal.score!.flip_score} size="sm" showLabel={false} />
                <div>
                  <p className="text-xs text-gray-500">SharkScore</p>
                  <p className="text-lg font-bold text-gray-900">{deal.score!.flip_score}</p>
                </div>
              </div>
              <div className="text-right">
                {/* Badge source des données */}
                <div className="flex items-center justify-end gap-1.5 mb-0.5">
                  <span className="text-xs text-gray-500">Profit</span>
                  {deal.vinted_stats?.source_type === "vinted_real" && deal.vinted_stats?.nb_listings > 0 ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-green-500 text-white" title="Prix réels Vinted (neuf avec étiquette)">
                      VINTED
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-gray-200 text-gray-600" title="Estimation algorithmique">
                      ESTIMÉ
                    </span>
                  )}
                </div>
                <p className={cn(
                  "text-lg font-bold",
                  (deal.score?.score_breakdown?.estimated_margin_pct || 0) >= 0 ? "text-green-600" : "text-red-500"
                )}>
                  {deal.score?.score_breakdown?.estimated_margin_pct
                    ? `${(deal.score.score_breakdown.estimated_margin_pct >= 0 ? "+" : "")}${deal.score.score_breakdown.estimated_margin_pct.toFixed(0)}%`
                    : "—"}
                  {deal.score?.score_breakdown?.estimated_margin_euro && (
                    <span className="text-xs ml-1 text-gray-500">
                      ({deal.score.score_breakdown.estimated_margin_euro >= 0 ? "+" : ""}{deal.score.score_breakdown.estimated_margin_euro.toFixed(0)}€)
                    </span>
                  )}
                </p>
              </div>
            </div>

            {/* Stats clés en ligne */}
            <div className="grid grid-cols-3 gap-2 text-center py-2 border-t border-gray-200/50">
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Revente</p>
                <p className="text-sm font-semibold text-gray-900">
                  {deal.score?.recommended_price ? formatPrice(deal.score.recommended_price) : "—"}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Délai</p>
                <p className="text-sm font-semibold text-gray-900">
                  ~{deal.score?.estimated_sell_days || "?"}j
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Confiance</p>
                <p className="text-sm font-semibold text-gray-900">
                  {deal.score?.confidence ? `${(deal.score.confidence * 100).toFixed(0)}%` : "—"}
                </p>
              </div>
            </div>

            {/* Scores détaillés (barres compactes) */}
            {deal.score?.score_breakdown && (
              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 mt-2 pt-2 border-t border-gray-200/50">
                {deal.score.score_breakdown.discount_score !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-gray-500 w-12">Remise</span>
                    <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(deal.score.score_breakdown.discount_score, 100)}%` }} />
                    </div>
                  </div>
                )}
                {deal.score.score_breakdown.margin_score !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-gray-500 w-12">Marge</span>
                    <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className={cn("h-full rounded-full", (deal.score.score_breakdown.estimated_margin_pct || 0) >= 0 ? "bg-green-500" : "bg-red-400")} style={{ width: `${Math.min(deal.score.score_breakdown.margin_score, 100)}%` }} />
                    </div>
                  </div>
                )}
                {deal.score.score_breakdown.brand_score !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-gray-500 w-12">Marque</span>
                    <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: `${Math.min(deal.score.score_breakdown.brand_score, 100)}%` }} />
                    </div>
                  </div>
                )}
                {deal.score.score_breakdown.popularity_score !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-gray-500 w-12">Demande</span>
                    <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-pink-500 rounded-full" style={{ width: `${Math.min(deal.score.score_breakdown.popularity_score, 100)}%` }} />
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 mt-4">
          {isAuthenticated && (
            <Button
              variant="primary"
              size="sm"
              className={cn(
                "flex-1 transition-colors",
                isFavorite
                  ? "bg-green-600 hover:bg-green-700"
                  : "bg-orange-500 hover:bg-orange-600"
              )}
              onClick={() => toggleFavorite(dealIdNum)}
              disabled={isFavoriteLoading}
            >
              <Eye size={16} className="mr-1.5" />
              {isFavorite ? "Suivi" : "Tracker"}
            </Button>
          )}
          <Link href={deal.product_url} target="_blank" className={isAuthenticated ? "flex-1" : "w-full"}>
            <Button variant="outline" size="sm" className="w-full">
              <ExternalLink size={16} className="mr-1.5" />
              Voir
            </Button>
          </Link>
        </div>

        {/* Admin: Rescore button */}
        {isAdmin && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full mt-2 text-xs text-gray-500 hover:text-blue-600 hover:bg-blue-50"
            onClick={handleRescore}
            disabled={isRescoring}
          >
            <RefreshCw size={14} className={cn("mr-1.5", isRescoring && "animate-spin")} />
            {isRescoring ? "Analyse en cours..." : "Reanalyser les prix"}
          </Button>
        )}

        {/* Explication courte */}
        {deal.score?.explanation_short && (
          <p className="text-xs text-gray-500 mt-3 text-center italic">
            {deal.score.explanation_short}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// Version compacte pour le feed temps reel
export function DealCardCompact({ deal, isNew = false }: DealCardProps) {
  const { isAuthenticated } = useAuth();
  const { data: favoriteIds = [] } = useFavoriteIds();
  const { toggleFavorite, isLoading: isFavoriteLoading } = useToggleFavorite();

  const dealIdNum = parseInt(deal.id, 10);
  const isFavorite = favoriteIds.includes(dealIdNum);

  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:shadow-md transition-all",
        isNew && "ring-2 ring-green-500 ring-opacity-50 bg-green-50/50",
        deal.score?.recommended_action === "buy" && "ring-2 ring-green-500 bg-green-50/30"
      )}
    >
      {/* Image */}
      <div className="relative w-20 h-20 rounded-lg overflow-hidden flex-shrink-0">
        {deal.image_url ? (
          <Image
            src={proxyImageUrl(deal.image_url)}
            alt={deal.product_name}
            fill
            unoptimized
            className="object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gray-100 flex items-center justify-center text-gray-400 text-xs">
            N/A
          </div>
        )}
        {isNew && (
          <div className="absolute top-0 right-0 w-3 h-3 bg-green-500 rounded-full animate-ping" />
        )}
        {deal.score?.recommended_action === "buy" && !isNew && (
          <div className="absolute top-0 left-0 bg-green-500 text-white text-[8px] font-bold px-1 py-0.5 rounded-br">
            BUY
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <div>
            <p className="text-xs text-gray-500">{deal.brand}</p>
            <h4 className="font-semibold text-gray-900 truncate">{deal.product_name}</h4>
          </div>
          {deal.score?.recommended_action && (
            <ActionBadge action={deal.score.recommended_action} size="sm" />
          )}
        </div>

        <div className="flex items-center gap-4">
          <span className="text-lg font-bold text-gray-900">
            {formatPrice(deal.sale_price)}
          </span>
          {deal.score?.score_breakdown?.estimated_margin_pct && (
            <ProfitIndicator marginPct={deal.score.score_breakdown.estimated_margin_pct} size="sm" />
          )}
          <TimeIndicator date={deal.detected_at} size="sm" showExactDate />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {isAuthenticated && (
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              "px-3 transition-colors",
              isFavorite
                ? "text-green-600 bg-green-50 hover:bg-green-100"
                : "text-orange-500 hover:text-orange-600 hover:bg-orange-50"
            )}
            onClick={() => toggleFavorite(dealIdNum)}
            disabled={isFavoriteLoading}
            title={isFavorite ? "Retirer des favoris" : "Ajouter aux favoris"}
          >
            <Eye size={16} className="mr-1" />
            {isFavorite ? "Suivi" : "Tracker"}
          </Button>
        )}
        <Link href={deal.product_url} target="_blank">
          <Button variant="ghost" size="sm">
            <ExternalLink size={18} />
          </Button>
        </Link>
      </div>
    </div>
  );
}
