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
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { adminApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface SourceHealth {
  source: string;
  status: "healthy" | "warning" | "error";
  last_success?: string;
  consecutive_failures: number;
  success_rate_24h: number;
  last_error?: string;
  needs_repair: boolean;
}

interface HealthResponse {
  status: string;
  sources: SourceHealth[];
  summary: {
    total: number;
    healthy: number;
    warning: number;
    error: number;
  };
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

  const { data: healthData, isLoading, refetch } = useQuery<HealthResponse>({
    queryKey: ["admin", "scraping-health"],
    queryFn: async () => {
      const { data } = await adminApi.scrapingHealth();
      return data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  const repairAllMutation = useMutation({
    mutationFn: async () => {
      return adminApi.repairAllSources();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "scraping-health"] });
    },
  });

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

  const sources = healthData?.sources || [];
  const summary = healthData?.summary || { total: 0, healthy: 0, warning: 0, error: 0 };
  const hasErrors = summary.error > 0 || summary.warning > 0;

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
          {hasErrors && (
            <Button
              size="sm"
              onClick={() => repairAllMutation.mutate()}
              disabled={repairAllMutation.isPending}
              className="gap-1 bg-orange-500 hover:bg-orange-600"
            >
              {repairAllMutation.isPending ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <Wrench size={14} />
              )}
              <span className="hidden sm:inline">Auto-Repair</span>
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0 sm:pt-0">
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-2 sm:gap-4 mb-4">
          <div className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-gray-900">{summary.total}</p>
            <p className="text-xs text-gray-500">Total</p>
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
        </div>

        {/* Sources List */}
        {isLoading ? (
          <div className="flex justify-center py-8">
            <RefreshCw className="animate-spin text-gray-400" size={24} />
          </div>
        ) : sources.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity size={48} className="mx-auto mb-4 opacity-50" />
            <p>Aucune source configuree</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sources.map((source) => (
              <div
                key={source.source}
                className={cn(
                  "border rounded-lg overflow-hidden transition-all",
                  source.status === "error"
                    ? "border-red-200 bg-red-50/30"
                    : source.status === "warning"
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
                    {getStatusIcon(source.status)}
                    <div>
                      <p className="font-medium text-sm sm:text-base capitalize">
                        {source.source}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Clock size={12} />
                        {formatTimeAgo(source.last_success)}
                        <span className="hidden sm:inline">
                          | Taux: {source.success_rate_24h.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "px-2 py-0.5 text-xs rounded-full border",
                        getStatusBadge(source.status)
                      )}
                    >
                      {source.status === "healthy"
                        ? "OK"
                        : source.status === "warning"
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
                        <span className="text-gray-500">Echecs consecutifs:</span>
                        <span
                          className={cn(
                            "ml-2 font-medium",
                            source.consecutive_failures > 0 ? "text-red-600" : "text-green-600"
                          )}
                        >
                          {source.consecutive_failures}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Taux de succes (24h):</span>
                        <span
                          className={cn(
                            "ml-2 font-medium",
                            source.success_rate_24h >= 80
                              ? "text-green-600"
                              : source.success_rate_24h >= 50
                              ? "text-yellow-600"
                              : "text-red-600"
                          )}
                        >
                          {source.success_rate_24h.toFixed(1)}%
                        </span>
                      </div>
                    </div>

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
            ))}
          </div>
        )}

        {/* Auto-repair status */}
        {repairAllMutation.isSuccess && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            <CheckCircle size={16} className="inline mr-2" />
            Auto-repair lance avec succes. Les reparations sont en cours en arriere-plan.
          </div>
        )}

        {repairAllMutation.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <XCircle size={16} className="inline mr-2" />
            Erreur lors du lancement de l&apos;auto-repair.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
