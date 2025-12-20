"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { ExternalLink, Eye, Zap, Heart, Clock } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SourceBadge, TimeIndicator } from "@/components/ui/indicators";

import { formatPrice, cn, proxyImageUrl } from "@/lib/utils";
import { useFavoriteIds, useToggleFavorite } from "@/hooks/use-favorites";
import { useAuth } from "@/hooks/use-auth";
import { Deal } from "../../types";

// === TRACKING SILENCIEUX ===
const trackEvent = async (dealId: number, eventType: string, value?: number) => {
  try {
    const sessionId = localStorage.getItem("sharkted_session") || generateSessionId();
    localStorage.setItem("sharkted_session", sessionId);
    
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/tracking/event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        deal_id: dealId,
        event_type: eventType,
        value,
        session_id: sessionId,
      }),
    });
  } catch (e) {
    // Silencieux - ne jamais bloquer l'UX
  }
};

const generateSessionId = () => {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
};

export interface DealCardProps {
  deal: Deal;
  isNew?: boolean;
  compact?: boolean;
}

export function DealCard({ deal, isNew = false }: DealCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [hasTrackedView, setHasTrackedView] = useState(false);
  const viewStartTime = useRef<number | null>(null);
  
  const { isAuthenticated } = useAuth();
  const { data: favoriteIds = [] } = useFavoriteIds();
  const { toggleFavorite, isLoading: isFavoriteLoading } = useToggleFavorite();

  const dealIdNum = parseInt(deal.id, 10);
  const isFavorite = favoriteIds.includes(dealIdNum);
  
  // Calculer si c'est une bonne affaire basée sur la décote
  const discountPct = deal.discount_pct || 0;
  const isGreatDeal = discountPct >= 50;
  const isGoodDeal = discountPct >= 30 && discountPct < 50;

  // Tracker les interactions
  useEffect(() => {
    if (isHovered && !hasTrackedView) {
      viewStartTime.current = Date.now();
      trackEvent(dealIdNum, "view");
      setHasTrackedView(true);
    }
    
    return () => {
      if (viewStartTime.current && hasTrackedView) {
        const viewTime = (Date.now() - viewStartTime.current) / 1000;
        if (viewTime > 2) { // Track si > 2s
          trackEvent(dealIdNum, "view_time", viewTime);
        }
      }
    };
  }, [isHovered, hasTrackedView, dealIdNum]);

  const handleClickOut = () => {
    trackEvent(dealIdNum, "click_out");
  };

  const handleFavorite = () => {
    const eventType = isFavorite ? "favorite_remove" : "favorite_add";
    trackEvent(dealIdNum, eventType);
    toggleFavorite(dealIdNum);
  };

  return (
    <Card
      className={cn(
        "overflow-hidden transition-all duration-300 group relative bg-white",
        isHovered ? "shadow-xl scale-[1.02]" : "hover:shadow-lg",
        isNew && "ring-2 ring-blue-500 ring-opacity-50",
        isGreatDeal && !isNew && "ring-2 ring-green-500/40"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Badge NOUVEAU */}
      {isNew && (
        <div className="absolute top-0 left-0 z-20 bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-br-lg flex items-center gap-1">
          <Zap size={12} />
          NOUVEAU
        </div>
      )}

      {/* Badge grosse décote */}
      {isGreatDeal && !isNew && (
        <div className="absolute top-0 left-0 z-20 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xs font-bold px-3 py-1.5 rounded-br-lg flex items-center gap-1">
          <span className="text-base">🔥</span>
          -{discountPct.toFixed(0)}%
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

        {/* Décote Badge - Top Left (si pas grosse promo) */}
        {discountPct > 0 && !isGreatDeal && !isNew && (
          <div className="absolute top-3 left-3 z-10">
            <div className={cn(
              "backdrop-blur rounded-lg px-3 py-1.5 shadow-lg font-bold text-sm",
              isGoodDeal 
                ? "bg-yellow-500/90 text-white" 
                : "bg-white/95 text-gray-800"
            )}>
              -{discountPct.toFixed(0)}%
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
          <div className="bg-black/70 backdrop-blur rounded-lg px-2 py-1 flex items-center gap-1.5">
            <Clock size={12} className="text-gray-300" />
            <TimeIndicator date={deal.detected_at} size="sm" />
          </div>
        </div>

        {/* Favoris Button - Bottom Right (visible on hover) */}
        {isAuthenticated && (
          <div
            className={cn(
              "absolute bottom-3 right-3 z-10 transition-all duration-200",
              isHovered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
            )}
          >
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "shadow-lg h-9 w-9 p-0",
                isFavorite 
                  ? "bg-red-500 text-white hover:bg-red-600" 
                  : "bg-white/90 text-gray-700 hover:bg-white"
              )}
              onClick={handleFavorite}
              disabled={isFavoriteLoading}
            >
              <Heart size={16} fill={isFavorite ? "currentColor" : "none"} />
            </Button>
          </div>
        )}
      </div>

      <CardContent className="p-4">
        {/* Brand & Name */}
        <div className="mb-3">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">
            {deal.brand}
          </p>
          <h3 className="font-bold text-gray-900 line-clamp-2 leading-tight text-sm">
            {deal.product_name}
          </h3>
        </div>

        {/* Prix */}
        <div className="flex items-baseline gap-3 mb-4">
          <span className="text-2xl font-bold text-gray-900">
            {formatPrice(deal.sale_price)}
          </span>
          {deal.original_price && deal.original_price > deal.sale_price && (
            <span className="text-sm text-gray-400 line-through">
              {formatPrice(deal.original_price)}
            </span>
          )}
        </div>

        {/* Tailles disponibles (si présentes) */}
        {deal.sizes_available && deal.sizes_available.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-1">Tailles disponibles</p>
            <div className="flex flex-wrap gap-1">
              {deal.sizes_available.slice(0, 6).map((size, idx) => (
                <span 
                  key={idx} 
                  className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded"
                >
                  {size}
                </span>
              ))}
              {deal.sizes_available.length > 6 && (
                <span className="text-xs text-gray-400">+{deal.sizes_available.length - 6}</span>
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Link href={deal.product_url} target="_blank" className="flex-1" onClick={handleClickOut}>
            <Button 
              variant="primary" 
              size="sm" 
              className={cn(
                "w-full font-semibold",
                isGreatDeal 
                  ? "bg-green-600 hover:bg-green-700" 
                  : "bg-blue-600 hover:bg-blue-700"
              )}
            >
              <ExternalLink size={16} className="mr-1.5" />
              Voir le deal
            </Button>
          </Link>
          
          {isAuthenticated && (
            <Button
              variant="outline"
              size="sm"
              className={cn(
                "transition-colors",
                isFavorite && "border-green-500 text-green-600"
              )}
              onClick={handleFavorite}
              disabled={isFavoriteLoading}
            >
              <Eye size={16} />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Version compacte pour le feed temps réel
export function DealCardCompact({ deal, isNew = false }: DealCardProps) {
  const { isAuthenticated } = useAuth();
  const { data: favoriteIds = [] } = useFavoriteIds();
  const { toggleFavorite, isLoading: isFavoriteLoading } = useToggleFavorite();

  const dealIdNum = parseInt(deal.id, 10);
  const isFavorite = favoriteIds.includes(dealIdNum);
  const discountPct = deal.discount_pct || 0;
  const isGreatDeal = discountPct >= 50;

  const handleClickOut = () => {
    trackEvent(dealIdNum, "click_out");
  };

  const handleFavorite = () => {
    const eventType = isFavorite ? "favorite_remove" : "favorite_add";
    trackEvent(dealIdNum, eventType);
    toggleFavorite(dealIdNum);
  };

  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:shadow-md transition-all",
        isNew && "ring-2 ring-blue-500 ring-opacity-50 bg-blue-50/30",
        isGreatDeal && !isNew && "ring-2 ring-green-500/40 bg-green-50/20"
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
          <div className="absolute top-0 right-0 w-3 h-3 bg-blue-500 rounded-full animate-ping" />
        )}
        {/* Badge décote sur image */}
        {discountPct >= 30 && (
          <div className={cn(
            "absolute bottom-0 left-0 right-0 text-center text-xs font-bold py-0.5",
            isGreatDeal ? "bg-green-500 text-white" : "bg-yellow-500 text-white"
          )}>
            -{discountPct.toFixed(0)}%
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <div>
            <p className="text-xs text-blue-600 font-semibold">{deal.brand}</p>
            <h4 className="font-semibold text-gray-900 truncate text-sm">{deal.product_name}</h4>
          </div>
          {deal.source_name && (
            <SourceBadge source={deal.source_name} size="sm" />
          )}
        </div>

        <div className="flex items-center gap-3 mt-1">
          <span className="text-lg font-bold text-gray-900">
            {formatPrice(deal.sale_price)}
          </span>
          {discountPct > 0 && discountPct < 30 && (
            <span className="text-sm font-medium text-orange-500">
              -{discountPct.toFixed(0)}%
            </span>
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
              "px-2 transition-colors",
              isFavorite
                ? "text-red-500 bg-red-50 hover:bg-red-100"
                : "text-gray-400 hover:text-red-500 hover:bg-red-50"
            )}
            onClick={handleFavorite}
            disabled={isFavoriteLoading}
          >
            <Heart size={18} fill={isFavorite ? "currentColor" : "none"} />
          </Button>
        )}
        <Link href={deal.product_url} target="_blank" onClick={handleClickOut}>
          <Button variant="ghost" size="sm" className="text-blue-600 hover:bg-blue-50">
            <ExternalLink size={18} />
          </Button>
        </Link>
      </div>
    </div>
  );
}
