"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  ShoppingBag,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Bell,
  LayoutGrid,
  List,
  Filter,
  Search,
  ChevronRight,
  Activity,
  Flame,
  Sliders,
} from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DealCard, DealCardCompact } from "@/components/deals/deal-card";
import {
  FlipScoreCircle,
  DeltaIndicator,
  Sparkline,
  LiveDot,
  Skeleton,
} from "@/components/ui/indicators";
import { analyticsApi, dealsApi, scrapingApi } from "@/lib/api";
import { DashboardStats, Deal } from "@/types";

interface Source {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  total_deals_found: number;
  last_scraped_at: string | null;
  plan_required: string;
}
import { cn } from "@/lib/utils";

// Stat Card amelioree avec sparkline et delta
function StatCard({
  title,
  value,
  change,
  changeValue,
  icon: Icon,
  trend,
  sparklineData,
  highlight,
  onClick,
}: {
  title: string;
  value: string | number;
  change?: string;
  changeValue?: number;
  icon: React.ElementType;
  trend?: "up" | "down";
  sparklineData?: number[];
  highlight?: boolean;
  onClick?: () => void;
}) {
  return (
    <Card
      className={cn(
        "relative overflow-hidden transition-all duration-300 hover:shadow-lg cursor-pointer animate-fade-in-up",
        "hover:scale-[1.02] active:scale-[0.98]",
        highlight && "ring-2 ring-primary-500 bg-primary-50"
      )}
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              {title}
            </p>
            <div className="flex items-baseline gap-2 mt-2">
              <p className="text-3xl font-bold text-gray-900 transition-all duration-300">{value}</p>
              {changeValue !== undefined && (
                <DeltaIndicator value={changeValue} size="sm" />
              )}
            </div>
            {change && !changeValue && (
              <div className="flex items-center mt-2 text-sm">
                {trend === "up" ? (
                  <ArrowUpRight className="text-green-500 animate-bounce-soft" size={16} />
                ) : trend === "down" ? (
                  <ArrowDownRight className="text-red-500" size={16} />
                ) : null}
                <span
                  className={cn(
                    "font-medium",
                    trend === "up" ? "text-green-600" : trend === "down" ? "text-red-600" : "text-gray-500"
                  )}
                >
                  {change}
                </span>
              </div>
            )}
          </div>
          <div
            className={cn(
              "w-14 h-14 rounded-2xl flex items-center justify-center transition-transform duration-300 hover:scale-110",
              highlight ? "bg-primary-500 text-white shadow-lg shadow-primary-500/30" : "bg-gray-100 text-gray-600"
            )}
          >
            <Icon size={28} />
          </div>
        </div>
        {sparklineData && sparklineData.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <Sparkline
              data={sparklineData}
              width={200}
              height={32}
              color={trend === "up" ? "#22c55e" : trend === "down" ? "#ef4444" : "#6366f1"}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Live Feed Header avec statut temps reel
function LiveFeedHeader({
  isLive,
  lastUpdate,
  onRefresh,
  isRefreshing,
}: {
  isLive: boolean;
  lastUpdate?: string;
  onRefresh: () => void;
  isRefreshing: boolean;
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-bold text-gray-900 animate-fade-in">Feed en direct</h2>
        <div
          className={cn(
            "flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium transition-all duration-300",
            isLive ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
          )}
        >
          <LiveDot isLive={isLive} size="sm" />
          {isLive ? "Live" : "Pause"}
        </div>
        {lastUpdate && (
          <span className="text-sm text-gray-500 animate-fade-in">
            Maj: {lastUpdate}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="gap-2 transition-all duration-200 hover:scale-105 active:scale-95"
        >
          <RefreshCw size={16} className={cn(isRefreshing && "animate-spin")} />
          Actualiser
        </Button>
        <Link href="/dashboard/deals">
          <Button variant="primary" size="sm" className="gap-2 transition-all duration-200 hover:scale-105 active:scale-95">
            Voir tout
            <ChevronRight size={16} />
          </Button>
        </Link>
      </div>
    </div>
  );
}

// Quick Action Button
function QuickAction({
  icon: Icon,
  label,
  description,
  onClick,
  highlight,
}: {
  icon: React.ElementType;
  label: string;
  description: string;
  onClick?: () => void;
  highlight?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-4 p-4 rounded-xl border transition-all duration-300 text-left w-full",
        "hover:scale-[1.02] active:scale-[0.98]",
        highlight
          ? "border-primary-500 bg-primary-50 hover:bg-primary-100 shadow-lg shadow-primary-500/20"
          : "border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300 hover:shadow-md"
      )}
    >
      <div
        className={cn(
          "w-12 h-12 rounded-xl flex items-center justify-center transition-transform duration-300",
          highlight ? "bg-primary-500 text-white animate-pulse-slow" : "bg-gray-100 text-gray-600"
        )}
      >
        <Icon size={24} className={cn(highlight && "animate-bounce-soft")} />
      </div>
      <div>
        <p className="font-semibold text-gray-900">{label}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </button>
  );
}

export default function DashboardPage() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Fetch dashboard stats
  const { data: stats, refetch: refetchStats } = useQuery<DashboardStats>({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => {
      const { data } = await analyticsApi.dashboard();
      return data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch top deals
  const { data: topDeals, isLoading: dealsLoading, refetch: refetchDeals } = useQuery<Deal[]>({
    queryKey: ["deals", "top"],
    queryFn: async () => {
      const { data } = await dealsApi.getTopRecommended(8);
      return data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch sources
  const { data: sources } = useQuery<Source[]>({
    queryKey: ["scraping", "sources"],
    queryFn: async () => {
      const { data } = await scrapingApi.sources();
      return data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  // Handle manual refresh
  const handleRefresh = async () => {
    await Promise.all([refetchStats(), refetchDeals()]);
  };

  // Simulated sparkline data
  const dealsSparkline = [45, 52, 48, 61, 55, 70, stats?.deals_today || 65];
  const scoreSparkline = [62, 65, 68, 64, 72, 75, stats?.avg_flip_score || 70];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        title="Dashboard"
        subtitle="Surveillez vos opportunites de resell en temps reel"
      />

      <div className="p-6 lg:p-8 space-y-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Deals actifs"
            value={stats?.active_deals || 0}
            changeValue={12.5}
            icon={ShoppingBag}
            trend="up"
            sparklineData={dealsSparkline}
          />
          <StatCard
            title="Nouveaux aujourd'hui"
            value={stats?.deals_today || 0}
            change="vs hier"
            icon={Zap}
            trend="up"
            highlight
          />
          <StatCard
            title="Score moyen"
            value={`${(stats?.avg_flip_score || 0).toFixed(0)}/100`}
            changeValue={5.2}
            icon={Target}
            trend="up"
            sparklineData={scoreSparkline}
          />
          <StatCard
            title="Top deals"
            value={stats?.top_deals_count || 0}
            change="Score > 70"
            icon={Flame}
            trend="up"
          />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuickAction
            icon={Bell}
            label="Mes alertes"
            description="Voir les dernieres opportunites"
            onClick={() => window.location.href = "/dashboard/alerts"}
          />
          <QuickAction
            icon={Sliders}
            label="Mes preferences"
            description="Marges, tailles, categories"
            onClick={() => window.location.href = "/dashboard/settings"}
          />
          <QuickAction
            icon={Filter}
            label="Explorer les deals"
            description="Filtrer par marques, prix, score"
            onClick={() => window.location.href = "/dashboard/deals"}
          />
        </div>

        {/* Live Feed Section */}
        <section>
          <LiveFeedHeader
            isLive={true}
            lastUpdate={stats?.last_scan ? new Date(stats.last_scan).toLocaleTimeString('fr-FR') : undefined}
            onRefresh={handleRefresh}
            isRefreshing={dealsLoading}
          />

          {/* View Mode Toggle */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                {topDeals?.length || 0} deals recommandes
              </span>
            </div>
            <div className="flex items-center gap-1 bg-white border border-gray-200 p-1 rounded-lg">
              <button
                className={cn(
                  "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  viewMode === "grid"
                    ? "bg-primary-500 text-white"
                    : "text-gray-600 hover:bg-gray-100"
                )}
                onClick={() => setViewMode("grid")}
              >
                <LayoutGrid size={16} />
              </button>
              <button
                className={cn(
                  "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  viewMode === "list"
                    ? "bg-primary-500 text-white"
                    : "text-gray-600 hover:bg-gray-100"
                )}
                onClick={() => setViewMode("list")}
              >
                <List size={16} />
              </button>
            </div>
          </div>

          {/* Deals Grid/List */}
          {dealsLoading ? (
            <div className={cn(
              viewMode === "grid"
                ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                : "space-y-4"
            )}>
              {Array.from({ length: 4 }).map((_, i) => (
                viewMode === "grid" ? (
                  <div key={i} className="bg-white rounded-xl overflow-hidden border border-gray-100">
                    <Skeleton className="h-48 w-full rounded-none" />
                    <div className="p-4 space-y-3">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-6 w-1/2" />
                      <div className="flex gap-2">
                        <Skeleton className="h-8 w-20" />
                        <Skeleton className="h-8 w-16" />
                      </div>
                      <Skeleton className="h-10 w-full" />
                    </div>
                  </div>
                ) : (
                  <div key={i} className="flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-100">
                    <Skeleton className="h-20 w-20 rounded-lg flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-1/3" />
                      <Skeleton className="h-5 w-2/3" />
                      <Skeleton className="h-4 w-1/4" />
                    </div>
                    <div className="flex gap-2">
                      <Skeleton className="h-8 w-8 rounded-lg" />
                      <Skeleton className="h-8 w-8 rounded-lg" />
                    </div>
                  </div>
                )
              ))}
            </div>
          ) : topDeals && topDeals.length > 0 ? (
            viewMode === "grid" ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {topDeals.map((deal, index) => (
                  <DealCard
                    key={deal.id}
                    deal={deal}
                    isNew={index < 2}
                  />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {topDeals.map((deal, index) => (
                  <DealCardCompact
                    key={deal.id}
                    deal={deal}
                    isNew={index < 2}
                  />
                ))}
              </div>
            )
          ) : (
            <Card className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search size={32} className="text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Aucun deal recommande
              </h3>
              <p className="text-gray-500 mb-4">
                Les nouveaux deals apparaitront ici automatiquement
              </p>
              <Link href="/dashboard/deals">
                <Button variant="primary" className="gap-2">
                  <Filter size={16} />
                  Explorer tous les deals
                </Button>
              </Link>
            </Card>
          )}
        </section>

        {/* Bottom Section - Stats & Sources */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Overview */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <Activity size={20} className="text-primary-500" />
                Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <Activity size={24} className="text-gray-400" />
                </div>
                <p className="text-gray-500 text-sm">
                  Les statistiques de performance seront disponibles une fois que vous aurez commence a suivre vos deals.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Sources Status */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Activity size={20} className="text-primary-500" />
                  Sources de donnees
                </CardTitle>
                <span className="text-sm text-gray-500">
                  {sources?.filter(s => s.is_active).length || 0} actives
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {sources?.sort((a, b) => {
                  // Sort: FREE first, then by priority/name
                  if (a.plan_required !== b.plan_required) {
                    return a.plan_required === "free" ? -1 : 1;
                  }
                  return a.name.localeCompare(b.name);
                }).map((source) => (
                  <div
                    key={source.id}
                    className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "w-2.5 h-2.5 rounded-full",
                          source.is_active
                            ? "bg-green-500"
                            : "bg-red-500"
                        )}
                      />
                      <span className="font-medium text-gray-900">{source.name}</span>
                      {source.plan_required === "pro" && (
                        <span className="text-xs bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded font-medium">
                          PRO
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-500">
                        {source.total_deals_found} deals
                      </span>
                      <span className="text-xs text-gray-400">
                        {source.last_scraped_at
                          ? `il y a ${Math.round((Date.now() - new Date(source.last_scraped_at).getTime()) / 60000)} min`
                          : "jamais"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
