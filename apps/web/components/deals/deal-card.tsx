"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ExternalLink, ShoppingCart, Eye, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FlipScoreCircle,
  ProfitIndicator,
  PopularityIndicator,
  LiquidityIndicator,
  TimeIndicator,
  ActionBadge,
  SourceBadge,
  Sparkline,
  ScoreBreakdown,
} from "@/components/ui/indicators";
import { Deal } from "@/types";
import { formatPrice, cn } from "@/lib/utils";

interface DealCardProps {
  deal: Deal;
  onTrack?: (deal: Deal) => void;
  isNew?: boolean;
  compact?: boolean;
}

export function DealCard({ deal, onTrack, isNew = false }: DealCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const hasScore = deal.score && deal.score.flip_score > 0;
  const hasStats = deal.vinted_stats && deal.vinted_stats.nb_listings > 0;

  // Simuler des donnees de tendance pour le sparkline
  const trendData = hasStats
    ? [65, 70, 68, 75, 72, 80, deal.score?.flip_score || 75]
    : [];

  return (
    <Card
      className={cn(
        "overflow-hidden transition-all duration-300 group relative",
        isHovered ? "shadow-xl scale-[1.02]" : "hover:shadow-lg",
        isNew && "ring-2 ring-green-500 ring-opacity-50"
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

      {/* Image Container */}
      <div className="relative h-48 bg-gray-100 overflow-hidden">
        {deal.image_url ? (
          <Image
            src={deal.image_url}
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
            Pas d'image
          </div>
        )}

        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

        {/* FlipScore Badge - Top Left */}
        {hasScore && (
          <div className="absolute top-3 left-3 z-10">
            <div className="bg-white/95 backdrop-blur rounded-xl p-2 shadow-lg">
              <FlipScoreCircle score={deal.score!.flip_score} size="sm" showLabel={false} />
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
            <TimeIndicator date={deal.detected_at} size="sm" />
          </div>
        </div>

        {/* Quick Actions - Bottom Right (visible on hover) */}
        <div
          className={cn(
            "absolute bottom-3 right-3 z-10 flex gap-2 transition-all duration-200",
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
          <Button
            variant="primary"
            size="sm"
            className="bg-green-500 hover:bg-green-600 text-white shadow-lg h-9 w-9 p-0"
            onClick={() => onTrack?.(deal)}
          >
            <ShoppingCart size={16} />
          </Button>
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

        {/* Indicateurs de decision */}
        {hasStats && (
          <div className="space-y-3 mb-4">
            {/* Profit Indicator */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500 uppercase tracking-wider">Profit potentiel</span>
              <ProfitIndicator
                marginEuro={deal.vinted_stats!.margin_euro}
                marginPct={deal.vinted_stats!.margin_pct}
                size="sm"
              />
            </div>

            {/* Liquidite */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500 uppercase tracking-wider">Liquidite</span>
              <LiquidityIndicator
                score={deal.vinted_stats!.liquidity_score || 50}
                listings={deal.vinted_stats!.nb_listings}
                size="sm"
              />
            </div>

            {/* Tendance / Popularite */}
            {hasScore && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 uppercase tracking-wider">Demande</span>
                <div className="flex items-center gap-2">
                  {trendData.length > 0 && (
                    <Sparkline
                      data={trendData}
                      width={50}
                      height={16}
                      color={deal.score!.flip_score >= 70 ? "#22c55e" : "#eab308"}
                    />
                  )}
                  <PopularityIndicator
                    score={deal.score!.confidence || 60}
                    size="sm"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Stats Vinted compactes */}
        {hasStats && (
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Prix Vinted</p>
                <p className="text-sm font-bold text-gray-900">
                  {formatPrice(deal.vinted_stats!.price_median || 0)}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Annonces</p>
                <p className="text-sm font-bold text-gray-900">
                  {deal.vinted_stats!.nb_listings}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Delai vente</p>
                <p className="text-sm font-bold text-gray-900">
                  ~{deal.score?.estimated_sell_days || "?"}j
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Score Breakdown - Transparence sur le scoring */}
        {hasScore && (deal.score!.margin_score || deal.score!.liquidity_score || deal.score!.popularity_score) && (
          <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-3 mb-4">
            <ScoreBreakdown
              marginScore={deal.score!.margin_score}
              liquidityScore={deal.score!.liquidity_score}
              popularityScore={deal.score!.popularity_score}
              breakdown={deal.score!.score_breakdown}
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="primary"
            size="sm"
            className="flex-1 bg-primary-600 hover:bg-primary-700"
            onClick={() => onTrack?.(deal)}
          >
            <Eye size={16} className="mr-1.5" />
            Tracker
          </Button>
          <Link href={deal.product_url} target="_blank" className="flex-1">
            <Button variant="outline" size="sm" className="w-full">
              <ExternalLink size={16} className="mr-1.5" />
              Voir
            </Button>
          </Link>
        </div>

        {/* Explication courte */}
        {deal.score?.explanation_short && (
          <p className="text-xs text-gray-500 mt-3 text-center italic">
            {deal.score.explanation_short}
          </p>
        )}

        {/* Risques identifies */}
        {deal.score?.risks && deal.score.risks.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1 justify-center">
            {deal.score.risks.slice(0, 3).map((risk, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-[10px]"
              >
                {risk}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Version compacte pour le feed temps reel
export function DealCardCompact({ deal, onTrack, isNew = false }: DealCardProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:shadow-md transition-all",
        isNew && "ring-2 ring-green-500 ring-opacity-50 bg-green-50/50"
      )}
    >
      {/* Image */}
      <div className="relative w-20 h-20 rounded-lg overflow-hidden flex-shrink-0">
        {deal.image_url ? (
          <Image
            src={deal.image_url}
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
          {deal.vinted_stats?.margin_pct && (
            <ProfitIndicator marginPct={deal.vinted_stats.margin_pct} size="sm" />
          )}
          <TimeIndicator date={deal.detected_at} size="sm" />
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 flex-shrink-0">
        <Button variant="ghost" size="sm" onClick={() => onTrack?.(deal)}>
          <Eye size={18} />
        </Button>
        <Link href={deal.product_url} target="_blank">
          <Button variant="ghost" size="sm">
            <ExternalLink size={18} />
          </Button>
        </Link>
      </div>
    </div>
  );
}
