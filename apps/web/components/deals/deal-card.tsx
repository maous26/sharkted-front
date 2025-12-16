"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ExternalLink, Eye, Zap, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
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
import { DealProfitInfo } from "./deal-profit-info";

import { formatPrice, cn, proxyImageUrl } from "@/lib/utils";
import { useFavoriteIds, useToggleFavorite } from "@/hooks/use-favorites";
import { useAuth } from "@/hooks/use-auth";
import { Deal } from "../../types";

export interface DealCardProps {
  deal: Deal;
  isNew?: boolean;
  compact?: boolean;
}

// Composant pour afficher les details du scoring
function ScoringDetails({ deal }: { deal: Deal }) {
  const hasScore = deal.score && deal.score.flip_score > 0;

  if (!hasScore) return null;

  // Utilise les marges estimées du score autonome (plus de Vinted)
  const marginPct = deal.score?.score_breakdown?.estimated_margin_pct || deal.vinted_stats?.margin_pct || 0;
  const marginEuro = deal.score?.score_breakdown?.estimated_margin_euro || deal.vinted_stats?.margin_euro || 0;
  const isPositiveMargin = marginPct > 0;

  return (
    <div className="mt-4 border-t border-gray-100 pt-4">
      {/* Score Breakdown */}
      {hasScore && deal.score?.score_breakdown && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2 flex items-center gap-1">
            <Info size={12} />
            Breakdown du Score
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {deal.score.score_breakdown.discount_score !== undefined && (
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-[10px] text-gray-500">Remise</p>
                <div className="flex items-center gap-1">
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${Math.min(deal.score.score_breakdown.discount_score, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{deal.score.score_breakdown.discount_score?.toFixed(0)}</span>
                </div>
              </div>
            )}
            {deal.score.score_breakdown.margin_score !== undefined && (
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-[10px] text-gray-500">Marge</p>
                <div className="flex items-center gap-1">
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={cn("h-full rounded-full", isPositiveMargin ? "bg-green-500" : "bg-orange-500")}
                      style={{ width: `${Math.min(deal.score.score_breakdown.margin_score, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{deal.score.score_breakdown.margin_score?.toFixed(0)}</span>
                </div>
              </div>
            )}
            {/* Brand Score (remplace Liquidité Vinted) */}
            {deal.score.score_breakdown.brand_score !== undefined && (
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-[10px] text-gray-500">Marque</p>
                <div className="flex items-center gap-1">
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500 rounded-full"
                      style={{ width: `${Math.min(deal.score.score_breakdown.brand_score, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{deal.score.score_breakdown.brand_score?.toFixed(0)}</span>
                </div>
              </div>
            )}
            {/* Contextual Score */}
            {deal.score.score_breakdown.contextual_score !== undefined && (
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-[10px] text-gray-500">Contexte</p>
                <div className="flex items-center gap-1">
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cyan-500 rounded-full"
                      style={{ width: `${Math.min(deal.score.score_breakdown.contextual_score, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{deal.score.score_breakdown.contextual_score?.toFixed(0)}</span>
                </div>
              </div>
            )}
            {deal.score.score_breakdown.popularity_score !== undefined && (
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-[10px] text-gray-500">Popularité</p>
                <div className="flex items-center gap-1">
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-pink-500 rounded-full"
                      style={{ width: `${Math.min(deal.score.score_breakdown.popularity_score, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{deal.score.score_breakdown.popularity_score?.toFixed(0)}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Marge et prix recommandé - utilise les marges estimées du scoring autonome */}
      {(marginPct !== 0 || deal.score?.recommended_price) && (
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-3 mb-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {isPositiveMargin ? (
                <TrendingUp className="w-4 h-4 text-green-600" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500" />
              )}
              <span className="text-sm font-semibold">
                Marge estimée
              </span>
            </div>
            <div className={cn(
              "text-lg font-bold",
              isPositiveMargin ? "text-green-600" : "text-red-500"
            )}>
              {isPositiveMargin ? "+" : ""}{marginPct.toFixed(1)}%
              <span className="text-xs ml-1 text-gray-500">
                ({isPositiveMargin ? "+" : ""}{marginEuro.toFixed(2)}€)
              </span>
            </div>
          </div>

          {/* Prix de vente recommandé */}
          {deal.score?.recommended_price && deal.score.recommended_price > 0 && (
            <div className="flex items-center justify-between text-sm border-t border-gray-200 pt-2 mt-2">
              <span className="text-gray-600">Prix de vente optimal</span>
              <span className="font-semibold text-primary-600">
                {formatPrice(deal.score.recommended_price)}
              </span>
            </div>
          )}

          {/* Fourchette de prix */}
          {deal.score?.recommended_price_range && (
            <div className="grid grid-cols-3 gap-2 mt-2 text-center text-xs">
              {deal.score.recommended_price_range.aggressive && (
                <div className="bg-white/60 rounded p-1">
                  <p className="text-gray-500">Rapide</p>
                  <p className="font-medium">{formatPrice(deal.score.recommended_price_range.aggressive)}</p>
                </div>
              )}
              {deal.score.recommended_price_range.optimal && (
                <div className="bg-white/60 rounded p-1">
                  <p className="text-gray-500">Optimal</p>
                  <p className="font-semibold text-primary-600">{formatPrice(deal.score.recommended_price_range.optimal)}</p>
                </div>
              )}
              {deal.score.recommended_price_range.patient && (
                <div className="bg-white/60 rounded p-1">
                  <p className="text-gray-500">Patient</p>
                  <p className="font-medium">{formatPrice(deal.score.recommended_price_range.patient)}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Modèle de scoring */}
      {deal.score?.model_version && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-500">Scoring:</span>
          <span className={cn(
            "text-xs font-medium px-2 py-0.5 rounded-full",
            deal.score.model_version === "autonomous_v3"
              ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-600"
          )}>
            {deal.score.model_version === "autonomous_v3"
              ? "Autonome v3"
              : deal.score.model_version}
          </span>
        </div>
      )}

      {/* Risques */}
      {deal.score?.risks && deal.score.risks.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-semibold text-orange-600 uppercase tracking-wider mb-1 flex items-center gap-1">
            <AlertTriangle size={12} />
            Risques
          </h4>
          <ul className="text-xs text-gray-600 space-y-1">
            {deal.score.risks.map((risk, idx) => (
              <li key={idx} className="flex items-start gap-1">
                <span className="text-orange-400 mt-0.5">•</span>
                <span>{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Confidence et Model */}
      <div className="flex items-center justify-between text-xs text-gray-400 border-t border-gray-100 pt-2">
        {deal.score?.confidence && (
          <span>Confiance: {(deal.score.confidence * 100).toFixed(0)}%</span>
        )}
        {deal.score?.model_version && (
          <span className="bg-gray-100 px-2 py-0.5 rounded text-[10px]">
            {deal.score.model_version}
          </span>
        )}
      </div>
    </div>
  );
}

export function DealCard({ deal, isNew = false }: DealCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const { isAuthenticated } = useAuth();
  const { data: favoriteIds = [] } = useFavoriteIds();
  const { toggleFavorite, isLoading: isFavoriteLoading } = useToggleFavorite();

  const dealIdNum = parseInt(deal.id, 10);
  const isFavorite = favoriteIds.includes(dealIdNum);
  const hasScore = deal.score && deal.score.flip_score > 0;
  // Scoring autonome - plus besoin de vinted_stats
  const hasMarginData = hasScore && (deal.score?.score_breakdown?.estimated_margin_pct !== undefined);

  // Données de tendance simulées pour le sparkline
  const trendData = hasScore
    ? [65, 70, 68, 75, 72, 80, deal.score?.flip_score || 75]
    : [];

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

        {/* FlipScore Badge - Top Left */}
        {hasScore && !isNew && deal.score?.recommended_action !== "buy" && (
          <div className="absolute top-3 left-3 z-10">
            <div className="bg-white/95 backdrop-blur rounded-xl p-2 shadow-lg flex flex-col items-center gap-1">
              <FlipScoreCircle score={deal.score!.flip_score} size="sm" showLabel={false} />
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
            <TimeIndicator date={deal.detected_at} size="sm" />
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

        {/* Indicateurs de decision - Scoring Autonome */}
        {hasScore && (
          <div className="space-y-3 mb-4">
            {/* Profit & Market Info (Vinted vs Estimated) */}
            <div className="mb-2">
              <DealProfitInfo deal={deal} />
            </div>

            {/* Separator if needed, but DealProfitInfo includes its own box */}

            {/* Score Marque (remplace Liquidité Vinted) */}
            {deal.score?.score_breakdown?.brand_score !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 uppercase tracking-wider">Marque</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500 rounded-full"
                      style={{ width: `${deal.score.score_breakdown.brand_score}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{deal.score.score_breakdown.brand_score?.toFixed(0)}</span>
                </div>
              </div>
            )}

            {/* Tendance / Popularite */}
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
          </div>
        )}

        {/* Stats Scoring Autonome */}
        {hasScore && (
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Prix revente</p>
                <p className="text-sm font-bold text-gray-900">
                  {deal.score?.recommended_price ? formatPrice(deal.score.recommended_price) : "—"}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Marge</p>
                <p className={cn(
                  "text-sm font-bold",
                  (deal.score?.score_breakdown?.estimated_margin_pct || 0) >= 0 ? "text-green-600" : "text-red-500"
                )}>
                  {deal.score?.score_breakdown?.estimated_margin_pct
                    ? `${deal.score.score_breakdown.estimated_margin_pct.toFixed(0)}%`
                    : "—"}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase">Délai vente</p>
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

        {/* Bouton pour afficher les details du scoring */}
        {hasScore && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full flex items-center justify-center gap-1 text-xs text-gray-500 hover:text-gray-700 py-2 border-t border-gray-100 transition-colors"
          >
            {showDetails ? (
              <>
                <ChevronUp size={14} />
                Masquer les détails
              </>
            ) : (
              <>
                <ChevronDown size={14} />
                Voir les détails du scoring
              </>
            )}
          </button>
        )}

        {/* Scoring Details (collapsible) */}
        {showDetails && <ScoringDetails deal={deal} />}

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
          <TimeIndicator date={deal.detected_at} size="sm" />
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
