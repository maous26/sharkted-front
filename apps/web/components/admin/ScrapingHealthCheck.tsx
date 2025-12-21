"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  Clock,
  Wrench,
  Zap,
  ChevronDown,
  ChevronUp,
  Play,
  TrendingDown,
  DollarSign,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { adminApi, scrapingApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface SourceDetail {
  status: "ok" | "disabled" | "error" | "warning";
  last_status?: string;
  deals_found?: number;
  deals_count?: number;
  last_run?: string;
  needs_repair: boolean;
  last_error?: string;
  // Price stats
  price_success_rate?: number;
  missing_prices?: number;
}

interface HealthResponse {
  status: string;
  healthy_sources: string[];
  sources_needing_repair: string[];
  details: Record<string, SourceDetail>;
}

interface PriceStats {
  sources: Array<{
    source: string;
    total: number;
    with_original: number;
    with_discount: number;
    missing: number;
    success_rate: number;
  }>;
}

interface DiagnoseResult {
  source: string;
  diagnosis: string;
  suggested_fix?: string;
  auto_repair_available: boolean;
}

export function ScrapingHealthCheck() {
  const queryClient = useQueryClient();
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [diagnosing, setDiagnosing] = useState<string | null>(null);
  const [diagnoseResult, setDiagnoseResult] = useState<Record<string, DiagnoseResult>>({});
  const [isRunningScrap, setIsRunningScrap] = useState(false);
  const [scrapingMessage, setScrapingMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const { data: healthData, isLoading, refetch } = useQuery<HealthResponse>({
    queryKey: ["admin", "scraping-health"],
    queryFn: async () => {
      const { data } = await adminApi.scrapingHealth();
      return data;
    },
    refetchInterval: 60000,
  });

  const { data: priceStats } = useQuery<PriceStats>({
    queryKey: ["admin", "price-errors"],
    queryFn: async () => {
      try {
        const { data } = await adminApi.getPriceErrors();
        return data?.stats || { sources: [] };
      } catch {
        return { sources: [] };
      }
    },
    refetchInterval: 120000,
  });

  const repairAllMutation = useMutation({
    mutationFn: async () => {
      return adminApi.repairAllSources();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "scraping-health"] });
      setScrapingMessage({ type: "success", text: "Auto-repair lance avec succes!" });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
    onError: () => {
      setScrapingMessage({ type: "error", text: "Erreur lors de l'auto-repair" });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
  });

  const repairPricesMutation = useMutation({
    mutationFn: async () => {
      return adminApi.repairPrices();
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "price-errors"] });
      const result = response?.data?.result;
      setScrapingMessage({
        type: "success",
        text: `Prix repares: ${result?.repaired || 0} deals mis a jour`
      });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
    onError: () => {
      setScrapingMessage({ type: "error", text: "Erreur lors de la reparation des prix" });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
  });

  const runScrapingMutation = useMutation({
    mutationFn: async () => {
      return scrapingApi.run({ send_alerts: true });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin"] });
      setIsRunningScrap(false);
      setScrapingMessage({ type: "success", text: "Scraping lance avec succes!" });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
    onError: (error: Error) => {
      setIsRunningScrap(false);
      setScrapingMessage({ type: "error", text: error.message || "Erreur lors du scraping" });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
  });

  const handleRunScraping = () => {
    setIsRunningScrap(true);
    setScrapingMessage(null);
    runScrapingMutation.mutate();
  };

  const handleDiagnose = async (source: string) => {
    setDiagnosing(source);
    try {
      const { data } = await adminApi.diagnoseSource(source);
      setDiagnoseResult({ ...diagnoseResult, [source]: data });
      setExpandedSource(source);
    } catch (error) {
      console.error("Diagnose error:", error);
    }
    setDiagnosing(null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="text-green-500" size={18} />;
      case "warning":
        return <AlertTriangle className="text-yellow-500" size={18} />;
      case "error":
        return <XCircle className="text-red-500" size={18} />;
      default:
        return <Activity className="text-gray-400" size={18} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      healthy: "bg-green-100 text-green-700 border-green-200",
      warning: "bg-yellow-100 text-yellow-700 border-yellow-200",
      error: "bg-red-100 text-red-700 border-red-200",
    };
    return styles[status as keyof typeof styles] || "bg-gray-100 text-gray-600";
  };

  const formatTimeAgo = (dateString?: string) => {
    if (!dateString) return "Jamais";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `il y a ${diffMins} min`;
    if (diffHours < 24) return `il y a ${diffHours}h`;
    return `il y a ${diffDays}j`;
  };

  // Merge health data with price stats
  const details = healthData?.details || {};
  type PriceSource = PriceStats["sources"][0];
  const priceBySource = (priceStats?.sources || []).reduce((acc, s) => {
    acc[s.source] = s;
    return acc;
  }, {} as Record<string, PriceSource>);

  const sourcesList = Object.entries(details)
    .filter(([, detail]) => detail.status !== "disabled")
    .map(([source, detail]) => ({
      source,
      ...detail,
      priceStats: priceBySource[source],
    }));

  const summary = {
    total: Object.keys(details).filter((s) => details[s].status !== "disabled").length,
    healthy: healthData?.healthy_sources?.length || 0,
    warning: sourcesList.filter((s) => s.last_status === "partial").length,
    error: healthData?.sources_needing_repair?.length || 0,
  };

  // Price health summary
  const priceSummary = {
    totalMissing: (priceStats?.sources || []).reduce((sum, s) => sum + (s.missing || 0), 0),
    lowRateSources: (priceStats?.sources || []).filter(s => s.success_rate < 50).length,
  };

  const hasErrors = summary.error > 0 || summary.warning > 0 || priceSummary.lowRateSources > 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between p-4 sm:p-6">
        <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
          <Activity size={20} className="text-blue-600" />
          Scraping Health Check
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
            className="gap-1"
          >
            <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
            <span className="hidden sm:inline">Actualiser</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunScraping}
            disabled={isRunningScrap}
            className="gap-1"
          >
            {isRunningScrap ? (
              <RefreshCw size={14} className="animate-spin" />
            ) : (
              <Play size={14} />
            )}
            <span className="hidden sm:inline">Lancer Scraping</span>
          </Button>
          <Button
            size="sm"
            onClick={() => repairAllMutation.mutate()}
            disabled={repairAllMutation.isPending}
            className={cn(
              "gap-1",
              hasErrors
                ? "bg-orange-500 hover:bg-orange-600"
                : "bg-blue-500 hover:bg-blue-600"
            )}
          >
            {repairAllMutation.isPending ? (
              <RefreshCw size={14} className="animate-spin" />
            ) : (
              <Wrench size={14} />
            )}
            <span className="hidden sm:inline">Auto-Repair</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0 sm:pt-0">
        {/* Message feedback */}
        {scrapingMessage && (
          <div
            className={cn(
              "mb-4 p-3 rounded-lg text-sm font-medium",
              scrapingMessage.type === "success"
                ? "bg-green-100 text-green-800 border border-green-200"
                : "bg-red-100 text-red-800 border border-red-200"
            )}
          >
            {scrapingMessage.type === "success" ? (
              <CheckCircle size={14} className="inline mr-2" />
            ) : (
              <AlertTriangle size={14} className="inline mr-2" />
            )}
            {scrapingMessage.text}
          </div>
        )}

        {/* Summary Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-4 mb-4">
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-gray-900">{summary.total}</p>
            <p className="text-xs text-gray-500">Sources</p>
          </div>
          <div className="text-center p-2 sm:p-3 bg-green-50 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-green-600">{summary.healthy}</p>
            <p className="text-xs text-green-600">Healthy</p>
          </div>
          <div className="text-center p-2 sm:p-3 bg-yellow-50 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-yellow-600">{summary.warning}</p>
            <p className="text-xs text-yellow-600">Warning</p>
          </div>
          <div className="text-center p-2 sm:p-3 bg-red-50 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-red-600">{summary.error}</p>
            <p className="text-xs text-red-600">Error</p>
          </div>
          <div className="text-center p-2 sm:p-3 bg-orange-50 rounded-lg col-span-2 sm:col-span-1">
            <p className="text-lg sm:text-2xl font-bold text-orange-600">{priceSummary.totalMissing}</p>
            <p className="text-xs text-orange-600">Prix manquants</p>
          </div>
        </div>

        {/* Price Repair Button */}
        {priceSummary.totalMissing > 0 && (
          <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="flex items-center gap-2">
              <DollarSign size={18} className="text-orange-500" />
              <div>
                <p className="text-sm font-medium text-orange-800">
                  {priceSummary.totalMissing} deals sans prix original
                </p>
                <p className="text-xs text-orange-600">
                  {priceSummary.lowRateSources} sources avec taux &lt; 50%
                </p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="border-orange-300 text-orange-700 hover:bg-orange-100"
              onClick={() => repairPricesMutation.mutate()}
              disabled={repairPricesMutation.isPending}
            >
              {repairPricesMutation.isPending ? (
                <RefreshCw size={14} className="animate-spin mr-1" />
              ) : (
                <TrendingDown size={14} className="mr-1" />
              )}
              Reparer les prix
            </Button>
          </div>
        )}

        {/* Sources List */}
        {isLoading ? (
          <div className="flex justify-center py-8">
            <RefreshCw className="animate-spin text-gray-400" size={24} />
          </div>
        ) : sourcesList.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity size={48} className="mx-auto mb-4 opacity-50" />
            <p>Aucune source configuree</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sourcesList.map((source) => {
              const displayStatus =
                source.status === "ok"
                  ? source.last_status === "partial"
                    ? "warning"
                    : "healthy"
                  : source.status === "error"
                  ? "error"
                  : "warning";
              const dealsCount = source.deals_found || source.deals_count || 0;
              const priceRate = source.priceStats?.success_rate;

              return (
                <div
                  key={source.source}
                  className={cn(
                    "border rounded-lg overflow-hidden transition-all",
                    displayStatus === "error"
                      ? "border-red-200 bg-red-50/30"
                      : displayStatus === "warning"
                      ? "border-yellow-200 bg-yellow-50/30"
                      : "border-green-200 bg-green-50/30"
                  )}
                >
                  {/* Source Header */}
                  <div
                    className="flex items-center justify-between p-3 cursor-pointer hover:bg-white/50"
                    onClick={() =>
                      setExpandedSource(expandedSource === source.source ? null : source.source)
                    }
                  >
                    <div className="flex items-center gap-3">
                      {getStatusIcon(displayStatus)}
                      <div>
                        <p className="font-medium text-sm sm:text-base capitalize">
                          {source.source}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Clock size={12} />
                          {formatTimeAgo(source.last_run)}
                          <span className="hidden sm:inline">| {dealsCount} deals</span>
                          {priceRate !== undefined && (
                            <span className={cn(
                              "hidden sm:inline",
                              priceRate >= 80 ? "text-green-600" : priceRate >= 50 ? "text-yellow-600" : "text-red-600"
                            )}>
                              | Prix: {priceRate.toFixed(0)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Price rate badge */}
                      {priceRate !== undefined && priceRate < 80 && (
                        <span className={cn(
                          "px-2 py-0.5 text-xs rounded-full",
                          priceRate >= 50 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"
                        )}>
                          {priceRate.toFixed(0)}%
                        </span>
                      )}

                      <span
                        className={cn(
                          "px-2 py-0.5 text-xs rounded-full border",
                          getStatusBadge(displayStatus)
                        )}
                      >
                        {displayStatus === "healthy"
                          ? "OK"
                          : displayStatus === "warning"
                          ? "Warn"
                          : "Err"}
                      </span>

                      {source.needs_repair && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDiagnose(source.source);
                          }}
                          disabled={diagnosing === source.source}
                          className="h-7 px-2 text-xs"
                        >
                          {diagnosing === source.source ? (
                            <RefreshCw size={12} className="animate-spin" />
                          ) : (
                            <Zap size={12} />
                          )}
                        </Button>
                      )}

                      {expandedSource === source.source ? (
                        <ChevronUp size={16} className="text-gray-400" />
                      ) : (
                        <ChevronDown size={16} className="text-gray-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedSource === source.source && (
                    <div className="border-t p-3 bg-white/70 space-y-2 text-sm">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-gray-500">Dernier statut:</span>
                          <span
                            className={cn(
                              "ml-2 font-medium capitalize",
                              source.last_status === "success"
                                ? "text-green-600"
                                : source.last_status === "partial"
                                ? "text-yellow-600"
                                : "text-red-600"
                            )}
                          >
                            {source.last_status || "N/A"}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Deals trouves:</span>
                          <span className="ml-2 font-medium text-gray-900">{dealsCount}</span>
                        </div>
                      </div>

                      {/* Price Stats */}
                      {source.priceStats && (
                        <div className="p-2 bg-gray-50 rounded text-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-gray-600">Taux prix original:</span>
                            <span className={cn(
                              "font-medium",
                              source.priceStats.success_rate >= 80 ? "text-green-600" :
                              source.priceStats.success_rate >= 50 ? "text-yellow-600" : "text-red-600"
                            )}>
                              {source.priceStats.with_original}/{source.priceStats.total} ({source.priceStats.success_rate.toFixed(0)}%)
                            </span>
                          </div>
                          {source.priceStats.missing > 0 && (
                            <p className="text-orange-600 mt-1">
                              {source.priceStats.missing} deals sans prix original
                            </p>
                          )}
                        </div>
                      )}

                      {source.last_error && (
                        <div className="p-2 bg-red-50 rounded text-xs">
                          <span className="text-red-600 font-medium">Derniere erreur: </span>
                          <span className="text-red-700">{source.last_error}</span>
                        </div>
                      )}

                      {/* Diagnosis Result */}
                      {diagnoseResult[source.source] && (
                        <div className="p-2 bg-blue-50 rounded text-xs space-y-1">
                          <p className="font-medium text-blue-700">Diagnostic:</p>
                          <p className="text-blue-600">
                            {diagnoseResult[source.source].diagnosis}
                          </p>
                          {diagnoseResult[source.source].suggested_fix && (
                            <p className="text-blue-500 italic">
                              Fix: {diagnoseResult[source.source].suggested_fix}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Auto-repair status */}
        {repairAllMutation.isSuccess && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            <CheckCircle size={16} className="inline mr-2" />
            Auto-repair lance avec succes. Les reparations sont en cours en arriere-plan.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
