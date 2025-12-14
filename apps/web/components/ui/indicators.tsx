"use client";

import { cn } from "@/lib/utils";
import {
  TrendingUp,
  TrendingDown,
  Flame,
  Clock,
  Star,
  Zap,
  AlertTriangle,
  CheckCircle,
  Eye,
} from "lucide-react";

// Indicateur Live pulsant
interface LiveDotProps {
  isLive?: boolean;
  size?: "sm" | "md" | "lg";
  label?: string;
}

export function LiveDot({ isLive = true, size = "md", label }: LiveDotProps) {
  const sizeClasses = {
    sm: { dot: "w-2 h-2", text: "text-xs" },
    md: { dot: "w-2.5 h-2.5", text: "text-sm" },
    lg: { dot: "w-3 h-3", text: "text-base" },
  };

  const config = sizeClasses[size];

  return (
    <div className="inline-flex items-center gap-2">
      <span className="relative flex">
        <span
          className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-75",
            isLive ? "bg-green-400 animate-ping" : "bg-gray-400"
          )}
        />
        <span
          className={cn(
            "relative inline-flex rounded-full",
            config.dot,
            isLive ? "bg-green-500" : "bg-gray-500"
          )}
        />
      </span>
      {label && (
        <span className={cn(config.text, "font-medium", isLive ? "text-green-600" : "text-gray-500")}>
          {label}
        </span>
      )}
    </div>
  );
}

// Loading skeleton avec shimmer
interface SkeletonProps {
  className?: string;
  animated?: boolean;
}

export function Skeleton({ className, animated = true }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-md bg-gray-200",
        animated && "animate-shimmer bg-shimmer-gradient bg-[length:200%_100%]",
        className
      )}
    />
  );
}

// Badge "Nouveau" avec animation
interface NewBadgeProps {
  size?: "sm" | "md" | "lg";
  animated?: boolean;
}

export function NewBadge({ size = "md", animated = true }: NewBadgeProps) {
  const sizeClasses = {
    sm: "text-[10px] px-1.5 py-0.5",
    md: "text-xs px-2 py-0.5",
    lg: "text-sm px-2.5 py-1",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 bg-green-500 text-white font-bold rounded-full uppercase tracking-wider",
        sizeClasses[size],
        animated && "animate-fade-in"
      )}
    >
      <Zap size={size === "sm" ? 10 : size === "md" ? 12 : 14} className={cn(animated && "animate-pulse-fast")} />
      Nouveau
    </span>
  );
}

// Indicateur de rentabilite avec code couleur
interface ProfitIndicatorProps {
  marginEuro?: number;
  marginPct?: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  animated?: boolean;
}

export function ProfitIndicator({
  marginEuro,
  marginPct,
  size = "md",
  showLabel = true,
  animated = false,
}: ProfitIndicatorProps) {
  const getColor = () => {
    if (!marginPct) return "text-gray-400";
    if (marginPct >= 50) return "text-green-500";
    if (marginPct >= 30) return "text-green-400";
    if (marginPct >= 20) return "text-yellow-500";
    if (marginPct >= 10) return "text-orange-500";
    return "text-red-500";
  };

  const getBgColor = () => {
    if (!marginPct) return "bg-gray-100";
    if (marginPct >= 50) return "bg-green-100";
    if (marginPct >= 30) return "bg-green-50";
    if (marginPct >= 20) return "bg-yellow-50";
    if (marginPct >= 10) return "bg-orange-50";
    return "bg-red-50";
  };

  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5",
    md: "text-sm px-2 py-1",
    lg: "text-base px-3 py-1.5",
  };

  if (!marginPct && !marginEuro) return null;

  const isHighProfit = marginPct && marginPct >= 40;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-md font-semibold transition-all duration-300",
        getBgColor(),
        getColor(),
        sizeClasses[size],
        animated && isHighProfit && "animate-number-pop",
        isHighProfit && "shadow-sm"
      )}
    >
      {marginPct && marginPct > 0 ? (
        <TrendingUp size={size === "sm" ? 12 : size === "md" ? 14 : 16} className={cn(isHighProfit && "animate-bounce-soft")} />
      ) : (
        <TrendingDown size={size === "sm" ? 12 : size === "md" ? 14 : 16} />
      )}
      {marginEuro !== undefined && (
        <span>+{marginEuro.toFixed(0)}EUR</span>
      )}
      {marginPct !== undefined && (
        <span className="opacity-75">({marginPct.toFixed(0)}%)</span>
      )}
    </div>
  );
}

// Indicateur de popularite/tendance
interface PopularityIndicatorProps {
  score: number; // 0-100
  label?: string;
  size?: "sm" | "md" | "lg";
}

export function PopularityIndicator({
  score,
  label,
  size = "md",
}: PopularityIndicatorProps) {
  const getLevel = () => {
    if (score >= 80) return { text: "Tres forte", color: "text-green-500", bars: 5 };
    if (score >= 60) return { text: "Forte", color: "text-green-400", bars: 4 };
    if (score >= 40) return { text: "Moyenne", color: "text-yellow-500", bars: 3 };
    if (score >= 20) return { text: "Faible", color: "text-orange-500", bars: 2 };
    return { text: "Tres faible", color: "text-red-500", bars: 1 };
  };

  const level = getLevel();
  const barHeight = size === "sm" ? "h-2" : size === "md" ? "h-3" : "h-4";

  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((bar) => (
          <div
            key={bar}
            className={cn(
              "w-1 rounded-full transition-all",
              barHeight,
              bar <= level.bars ? level.color.replace("text-", "bg-") : "bg-gray-200"
            )}
          />
        ))}
      </div>
      {label !== undefined && (
        <span className={cn("text-xs font-medium", level.color)}>
          {label || level.text}
        </span>
      )}
    </div>
  );
}

// Indicateur de rarete
interface RarityIndicatorProps {
  level: "common" | "uncommon" | "rare" | "very_rare" | "legendary";
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
}

export function RarityIndicator({
  level,
  showLabel = true,
  size = "md",
}: RarityIndicatorProps) {
  const config = {
    common: { label: "Commun", color: "text-gray-500", bg: "bg-gray-100", icon: null },
    uncommon: { label: "Peu courant", color: "text-blue-500", bg: "bg-blue-100", icon: null },
    rare: { label: "Rare", color: "text-purple-500", bg: "bg-purple-100", icon: Star },
    very_rare: { label: "Tres rare", color: "text-orange-500", bg: "bg-orange-100", icon: Star },
    legendary: { label: "Legendaire", color: "text-yellow-500", bg: "bg-yellow-100", icon: Flame },
  };

  const { label, color, bg, icon: Icon } = config[level];
  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5",
    md: "text-sm px-2 py-1",
    lg: "text-base px-3 py-1.5",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-md font-medium",
        bg,
        color,
        sizeClasses[size]
      )}
    >
      {Icon && <Icon size={size === "sm" ? 12 : size === "md" ? 14 : 16} />}
      {showLabel && <span>{label}</span>}
    </div>
  );
}

// Indicateur de temps relatif avec urgence
interface TimeIndicatorProps {
  date: Date | string;
  showUrgent?: boolean;
  size?: "sm" | "md" | "lg";
}

export function TimeIndicator({
  date,
  showUrgent = true,
  size = "md",
}: TimeIndicatorProps) {
  const now = new Date();
  const then = new Date(date);

  // Handle invalid dates
  if (isNaN(then.getTime())) {
    return <span className="text-gray-400 text-sm">-</span>;
  }

  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  const getTimeText = () => {
    if (seconds < 10) return "A l'instant";
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}min`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}j`;
  };

  const isUrgent = showUrgent && seconds < 120; // < 2 minutes
  const isRecent = seconds < 300; // < 5 minutes

  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 transition-colors duration-200",
        sizeClasses[size],
        isUrgent ? "text-red-500 animate-urgency-flash" : isRecent ? "text-orange-500" : "text-gray-500"
      )}
    >
      <Clock size={size === "sm" ? 12 : size === "md" ? 14 : 16} className={cn(isUrgent && "animate-pulse-fast")} />
      <span className="font-medium">{getTimeText()}</span>
      {isUrgent && <Zap size={size === "sm" ? 10 : 12} className="text-yellow-500 animate-bounce-soft" />}
    </div>
  );
}

// Indicateur de liquidite
interface LiquidityIndicatorProps {
  score: number; // 0-100
  listings?: number;
  size?: "sm" | "md" | "lg";
}

export function LiquidityIndicator({
  score,
  listings,
  size = "md",
}: LiquidityIndicatorProps) {
  const getLevel = () => {
    if (score >= 80) return { text: "Vente rapide", color: "text-green-500", icon: Zap };
    if (score >= 60) return { text: "Bonne liquidite", color: "text-green-400", icon: CheckCircle };
    if (score >= 40) return { text: "Liquidite moyenne", color: "text-yellow-500", icon: Eye };
    if (score >= 20) return { text: "Vente lente", color: "text-orange-500", icon: AlertTriangle };
    return { text: "Difficile a vendre", color: "text-red-500", icon: AlertTriangle };
  };

  const level = getLevel();
  const Icon = level.icon;
  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div className={cn("inline-flex items-center gap-1", sizeClasses[size], level.color)}>
      <Icon size={size === "sm" ? 12 : size === "md" ? 14 : 16} />
      <span className="font-medium">{level.text}</span>
      {listings !== undefined && (
        <span className="opacity-60">({listings} annonces)</span>
      )}
    </div>
  );
}

// FlipScore circulaire
interface FlipScoreCircleProps {
  score: number;
  size?: "sm" | "md" | "lg" | "xl";
  showLabel?: boolean;
  animated?: boolean;
  glowOnHigh?: boolean;
}

export function FlipScoreCircle({
  score,
  size = "md",
  showLabel = true,
  animated = true,
  glowOnHigh = true,
}: FlipScoreCircleProps) {
  const getColor = () => {
    if (score >= 80) return { stroke: "#22c55e", text: "text-green-500", label: "Excellent", glow: "shadow-green-500/50" };
    if (score >= 60) return { stroke: "#eab308", text: "text-yellow-500", label: "Bon", glow: "shadow-yellow-500/50" };
    if (score >= 40) return { stroke: "#f97316", text: "text-orange-500", label: "Moyen", glow: "" };
    return { stroke: "#ef4444", text: "text-red-500", label: "Faible", glow: "" };
  };

  const color = getColor();
  const sizeConfig = {
    sm: { size: 40, stroke: 3, fontSize: "text-xs" },
    md: { size: 56, stroke: 4, fontSize: "text-sm" },
    lg: { size: 72, stroke: 5, fontSize: "text-base" },
    xl: { size: 96, stroke: 6, fontSize: "text-lg" },
  };

  const config = sizeConfig[size];
  const radius = (config.size - config.stroke) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;
  const isHighScore = score >= 70;

  return (
    <div className={cn("flex flex-col items-center", animated && "animate-fade-in")}>
      <div
        className={cn(
          "relative rounded-full transition-shadow duration-500",
          glowOnHigh && isHighScore && "shadow-lg",
          glowOnHigh && isHighScore && color.glow
        )}
        style={{ width: config.size, height: config.size }}
      >
        <svg className="transform -rotate-90" width={config.size} height={config.size}>
          <circle
            cx={config.size / 2}
            cy={config.size / 2}
            r={radius}
            stroke="#e5e7eb"
            strokeWidth={config.stroke}
            fill="none"
          />
          <circle
            cx={config.size / 2}
            cy={config.size / 2}
            r={radius}
            stroke={color.stroke}
            strokeWidth={config.stroke}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={cn(
              "transition-all duration-700 ease-out",
              animated && "animate-score-fill"
            )}
            style={{ "--score-offset": offset } as React.CSSProperties}
          />
        </svg>
        <div
          className={cn(
            "absolute inset-0 flex items-center justify-center font-bold",
            config.fontSize,
            color.text,
            animated && "animate-number-pop"
          )}
        >
          {score.toFixed(0)}
        </div>
      </div>
      {showLabel && (
        <span className={cn("mt-1 font-medium transition-colors duration-300", config.fontSize, color.text)}>
          {color.label}
        </span>
      )}
    </div>
  );
}

// Badge de recommandation avec icone
interface ActionBadgeProps {
  action: "buy" | "watch" | "ignore";
  size?: "sm" | "md" | "lg";
  animated?: boolean;
}

export function ActionBadge({
  action,
  size = "md",
  animated = false,
}: ActionBadgeProps) {
  const config = {
    buy: {
      label: "Acheter",
      color: "text-white",
      bg: "bg-green-500",
      icon: Zap,
      hoverBg: "hover:bg-green-600",
      glowClass: "animate-glow",
    },
    watch: {
      label: "Surveiller",
      color: "text-white",
      bg: "bg-yellow-500",
      icon: Eye,
      hoverBg: "hover:bg-yellow-600",
      glowClass: "",
    },
    ignore: {
      label: "Ignorer",
      color: "text-white",
      bg: "bg-gray-500",
      icon: null,
      hoverBg: "hover:bg-gray-600",
      glowClass: "",
    },
  };

  const { label, color, bg, icon: Icon, hoverBg, glowClass } = config[action];
  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-1.5",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-semibold transition-all duration-300",
        bg,
        color,
        hoverBg,
        sizeClasses[size],
        animated && action === "buy" && glowClass,
        "hover:scale-105 active:scale-95"
      )}
    >
      {Icon && (
        <Icon
          size={size === "sm" ? 12 : size === "md" ? 14 : 16}
          className={cn(animated && action === "buy" && "animate-pulse-fast")}
        />
      )}
      <span>{label}</span>
    </div>
  );
}

// Sparkline simple pour tendance
interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  showDot?: boolean;
}

export function Sparkline({
  data,
  width = 80,
  height = 24,
  color = "#22c55e",
  showDot = true,
}: SparklineProps) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  });

  const lastPoint = points[points.length - 1].split(",");

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {showDot && (
        <circle
          cx={lastPoint[0]}
          cy={lastPoint[1]}
          r={3}
          fill={color}
        />
      )}
    </svg>
  );
}

// Indicateur de delta/variation
interface DeltaIndicatorProps {
  value: number;
  suffix?: string;
  size?: "sm" | "md" | "lg";
}

export function DeltaIndicator({
  value,
  suffix = "%",
  size = "md",
}: DeltaIndicatorProps) {
  const isPositive = value > 0;
  const isNeutral = value === 0;

  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-0.5 font-medium",
        sizeClasses[size],
        isPositive ? "text-green-500" : isNeutral ? "text-gray-500" : "text-red-500"
      )}
    >
      {isPositive ? (
        <TrendingUp size={size === "sm" ? 12 : size === "md" ? 14 : 16} />
      ) : isNeutral ? null : (
        <TrendingDown size={size === "sm" ? 12 : size === "md" ? 14 : 16} />
      )}
      <span>
        {isPositive ? "+" : ""}
        {value.toFixed(1)}
        {suffix}
      </span>
    </div>
  );
}

// Source badge avec logo
interface SourceBadgeProps {
  source: string;
  size?: "sm" | "md" | "lg";
}

export function SourceBadge({ source, size = "md" }: SourceBadgeProps) {
  const sourceConfig: Record<string, { color: string; bg: string }> = {
    nike: { color: "text-gray-900", bg: "bg-gray-100" },
    adidas: { color: "text-black", bg: "bg-yellow-100" },
    zalando: { color: "text-orange-600", bg: "bg-orange-100" },
    courir: { color: "text-blue-600", bg: "bg-blue-100" },
    footlocker: { color: "text-red-600", bg: "bg-red-100" },
    size: { color: "text-purple-600", bg: "bg-purple-100" },
    jdsports: { color: "text-black", bg: "bg-yellow-100" },
    snipes: { color: "text-orange-600", bg: "bg-orange-100" },
    "ralph lauren": { color: "text-blue-900", bg: "bg-blue-100" },
    ralphlauren: { color: "text-blue-900", bg: "bg-blue-100" },
    galerieslafayette: { color: "text-black", bg: "bg-gray-100" },
    printemps: { color: "text-pink-600", bg: "bg-pink-100" },
  };

  const config = sourceConfig[source.toLowerCase()] || { color: "text-gray-600", bg: "bg-gray-100" };
  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5",
    md: "text-xs px-2 py-1",
    lg: "text-sm px-3 py-1.5",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded font-medium uppercase tracking-wider",
        config.color,
        config.bg,
        sizeClasses[size]
      )}
    >
      {source}
    </span>
  );
}

// Score breakdown display for transparency
interface ScoreBreakdownProps {
  marginScore?: number;
  liquidityScore?: number;
  popularityScore?: number;
  breakdown?: {
    margin_score?: number;
    liquidity_score?: number;
    popularity_score?: number;
    contextual_bonus?: number;
    size_bonus?: number;
    brand_bonus?: number;
    discount_bonus?: number;
  };
  compact?: boolean;
}

export function ScoreBreakdown({
  marginScore,
  liquidityScore,
  popularityScore,
  breakdown,
  compact = false,
}: ScoreBreakdownProps) {
  const scores = [
    { label: "Marge", score: marginScore, weight: 40, icon: TrendingUp, color: "text-green-500" },
    { label: "Liquidite", score: liquidityScore, weight: 30, icon: Zap, color: "text-blue-500" },
    { label: "Popularite", score: popularityScore, weight: 20, icon: Flame, color: "text-orange-500" },
  ];

  const bonuses = breakdown ? [
    { label: "Contexte", value: breakdown.contextual_bonus, icon: CheckCircle },
    { label: "Tailles", value: breakdown.size_bonus, icon: Star },
    { label: "Marque", value: breakdown.brand_bonus, icon: Star },
  ].filter(b => b.value && b.value > 0) : [];

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        {scores.map(({ label, score, icon: Icon, color }) => (
          score !== undefined && score !== null && (
            <div key={label} className="flex items-center gap-1" title={`${label}: ${score.toFixed(0)}/100`}>
              <Icon size={12} className={color} />
              <span className="text-xs font-medium text-gray-600">{score.toFixed(0)}</span>
            </div>
          )
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">Pourquoi ce score?</p>
      <div className="space-y-1.5">
        {scores.map(({ label, score, weight, icon: Icon, color }) => (
          score !== undefined && score !== null && (
            <div key={label} className="flex items-center gap-2">
              <Icon size={14} className={color} />
              <span className="text-xs text-gray-600 w-16">{label}</span>
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all duration-500", color.replace("text-", "bg-"))}
                  style={{ width: `${score}%` }}
                />
              </div>
              <span className="text-xs font-medium text-gray-700 w-8 text-right">{score.toFixed(0)}</span>
              <span className="text-[10px] text-gray-400">({weight}%)</span>
            </div>
          )
        ))}
      </div>
      {bonuses.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {bonuses.map(({ label, value, icon: Icon }) => (
            <div
              key={label}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-green-50 text-green-700 rounded text-[10px] font-medium"
            >
              <Icon size={10} />
              +{value} {label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
