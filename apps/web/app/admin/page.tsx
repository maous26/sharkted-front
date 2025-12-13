"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw,
  Settings,
  Database,
  Activity,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Pause,
  Trash2,
  Save,
  Globe,
  Webhook,
  Clock,
  BarChart3,
  Shield,
  LogOut,
  Crown,
  Network,
  Zap,
  FileText,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { scrapingApi, analyticsApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import { LiveDot } from "@/components/ui/indicators";
import { useAuth } from "@/hooks/use-auth";

interface ScrapingSource {
  id: string;
  name: string;
  slug: string;
  base_url: string;
  is_active: boolean;
  priority: number;
  last_scraped_at?: string;
  last_error?: string;
  total_deals_found: number;
  plan_required?: string; // "free" or "pro"
}

interface SystemStatus {
  database: "connected" | "error";
  scraping: "running" | "idle" | "error";
  last_scrape?: string;
  total_deals: number;
  total_users: number;
  active_sources: number;
}

interface SystemSettings {
  use_rotating_proxy: boolean;
  proxy_count: number;
  scrape_interval_minutes: number;
  max_concurrent_scrapers: number;
  min_margin_percent: number;
  min_flip_score: number;
}

interface ScrapingLogEntry {
  id: string;
  source_slug: string;
  source_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  deals_found: number;
  deals_new: number;
  deals_updated: number;
  error_message?: string;
  triggered_by: string;
  proxy_used: boolean;
}

interface ScrapingLogsResponse {
  logs: ScrapingLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

export default function AdminPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const queryClient = useQueryClient();
  const [isRunningScrap, setIsRunningScrap] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [scrapingMessage, setScrapingMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [editingSource, setEditingSource] = useState<ScrapingSource | null>(null);
  const [sourceSettings, setSourceSettings] = useState<{
    is_active: boolean;
    priority: number;
  }>({ is_active: true, priority: 1 });
  const [isTogglingProxy, setIsTogglingProxy] = useState(false);
  const [isReloadingProxies, setIsReloadingProxies] = useState(false);
  const [logsPage, setLogsPage] = useState(1);
  const [isDeletingLog, setIsDeletingLog] = useState<string | null>(null);
  const [isDeletingOldLogs, setIsDeletingOldLogs] = useState(false);

  // Check authentication and authorization
  const isAdmin = user?.plan === "PRO" || user?.plan === "AGENCY" || user?.plan === "pro" || user?.plan === "agency";

  // ALL HOOKS MUST BE CALLED BEFORE ANY CONDITIONAL RETURN
  // Fetch system status
  const { data: status } = useQuery<SystemStatus>({
    queryKey: ["admin", "status"],
    queryFn: async () => {
      // Simulated data - replace with actual API call
      return {
        database: "connected",
        scraping: "idle",
        last_scrape: new Date().toISOString(),
        total_deals: 1250,
        total_users: 45,
        active_sources: 6,
      };
    },
    refetchInterval: 10000,
    enabled: isAuthenticated && isAdmin,
  });

  // Fetch scraping sources
  const { data: sources, isLoading: sourcesLoading } = useQuery<ScrapingSource[]>({
    queryKey: ["admin", "sources"],
    queryFn: async () => {
      try {
        const { data } = await scrapingApi.sources();
        return data || [];
      } catch {
        return [];
      }
    },
    enabled: isAuthenticated && isAdmin,
  });

  // Fetch system settings
  const { data: systemSettings, refetch: refetchSettings } = useQuery<SystemSettings>({
    queryKey: ["admin", "settings"],
    queryFn: async () => {
      try {
        const { data } = await scrapingApi.getSettings();
        return data;
      } catch {
        return {
          use_rotating_proxy: false,
          proxy_count: 0,
          scrape_interval_minutes: 15,
          max_concurrent_scrapers: 3,
          min_margin_percent: 20,
          min_flip_score: 70,
        };
      }
    },
    enabled: isAuthenticated && isAdmin,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch scraping logs
  const { data: logsData, refetch: refetchLogs, isLoading: logsLoading } = useQuery<ScrapingLogsResponse>({
    queryKey: ["admin", "logs", logsPage],
    queryFn: async () => {
      try {
        const { data } = await scrapingApi.getLogs({ page: logsPage, page_size: 20 });
        return data;
      } catch {
        return { logs: [], total: 0, page: 1, page_size: 20 };
      }
    },
    enabled: isAuthenticated && isAdmin,
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  // Update source mutation
  const updateSourceMutation = useMutation({
    mutationFn: async ({ slug, data }: { slug: string; data: { is_active?: boolean; priority?: number } }) => {
      const response = await scrapingApi.updateSource(slug, data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "sources"] });
    },
    onError: (error: Error) => {
      console.error("Update source error:", error);
      setScrapingMessage({
        type: "error",
        text: error.message || "Erreur lors de la mise a jour",
      });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
  });

  // Run scraping mutation
  const runScrapingMutation = useMutation({
    mutationFn: async (sourcesToRun?: string[]) => {
      console.log("Starting scraping with sources:", sourcesToRun);
      const response = await scrapingApi.run({
        sources: sourcesToRun?.length ? sourcesToRun : undefined,
        send_alerts: true,
      });
      console.log("Scraping response:", response);
      return response;
    },
    onSuccess: (response) => {
      console.log("Scraping mutation success:", response);
      queryClient.invalidateQueries({ queryKey: ["admin"] });
      setIsRunningScrap(false);
      setScrapingMessage({
        type: "success",
        text: response.data?.message || "Scraping lance avec succes!",
      });
      // Clear message after 5 seconds
      setTimeout(() => setScrapingMessage(null), 5000);
    },
    onError: (error: Error) => {
      console.error("Scraping mutation error:", error);
      setIsRunningScrap(false);
      setScrapingMessage({
        type: "error",
        text: error.message || "Erreur lors du lancement du scraping",
      });
      setTimeout(() => setScrapingMessage(null), 5000);
    },
  });

  // Redirect effect
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/auth/login");
    } else if (!isAdmin) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isAdmin, router]);

  // Helper functions
  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  const handleRunScraping = (sourcesToRun?: string[]) => {
    console.log("handleRunScraping called with:", sourcesToRun);
    setScrapingMessage(null);
    setIsRunningScrap(true);
    runScrapingMutation.mutate(sourcesToRun);
  };

  const getSourceStatus = (source: ScrapingSource): "active" | "error" | "disabled" => {
    if (!source.is_active) return "disabled";
    if (source.last_error) return "error";
    return "active";
  };

  const handleOpenSourceSettings = (source: ScrapingSource) => {
    setEditingSource(source);
    setSourceSettings({
      is_active: source.is_active,
      priority: source.priority,
    });
  };

  const handleCloseSourceSettings = () => {
    setEditingSource(null);
  };

  const handleToggleSource = (source: ScrapingSource) => {
    updateSourceMutation.mutate(
      {
        slug: source.slug,
        data: { is_active: !source.is_active },
      },
      {
        onSuccess: () => {
          setScrapingMessage({
            type: "success",
            text: `Source ${source.name} ${source.is_active ? "desactivee" : "activee"}`,
          });
          setTimeout(() => setScrapingMessage(null), 3000);
        },
      }
    );
  };

  const handleSaveSourceSettings = () => {
    if (!editingSource) return;
    updateSourceMutation.mutate(
      {
        slug: editingSource.slug,
        data: sourceSettings,
      },
      {
        onSuccess: () => {
          setScrapingMessage({
            type: "success",
            text: `Parametres de ${editingSource.name} mis a jour`,
          });
          setTimeout(() => setScrapingMessage(null), 3000);
          handleCloseSourceSettings();
        },
      }
    );
  };

  const handleToggleProxy = async () => {
    setIsTogglingProxy(true);
    try {
      const newValue = !systemSettings?.use_rotating_proxy;
      await scrapingApi.updateSettings({ use_rotating_proxy: newValue });
      await refetchSettings();
      setScrapingMessage({
        type: "success",
        text: newValue ? "Mode proxy active" : "Mode proxy desactive",
      });
      setTimeout(() => setScrapingMessage(null), 3000);
    } catch (error) {
      setScrapingMessage({
        type: "error",
        text: "Erreur lors du changement de mode proxy",
      });
      setTimeout(() => setScrapingMessage(null), 5000);
    } finally {
      setIsTogglingProxy(false);
    }
  };

  const handleReloadProxies = async () => {
    setIsReloadingProxies(true);
    try {
      const { data } = await scrapingApi.reloadProxies();
      await refetchSettings();
      setScrapingMessage({
        type: data.success ? "success" : "error",
        text: data.message,
      });
      setTimeout(() => setScrapingMessage(null), 3000);
    } catch (error) {
      setScrapingMessage({
        type: "error",
        text: "Erreur lors du rechargement des proxies",
      });
      setTimeout(() => setScrapingMessage(null), 5000);
    } finally {
      setIsReloadingProxies(false);
    }
  };

  const handleDeleteLog = async (logId: string) => {
    setIsDeletingLog(logId);
    try {
      await scrapingApi.deleteLog(logId);
      await refetchLogs();
      setScrapingMessage({
        type: "success",
        text: "Log supprime",
      });
      setTimeout(() => setScrapingMessage(null), 3000);
    } catch (error) {
      setScrapingMessage({
        type: "error",
        text: "Erreur lors de la suppression du log",
      });
      setTimeout(() => setScrapingMessage(null), 5000);
    } finally {
      setIsDeletingLog(null);
    }
  };

  const handleDeleteOldLogs = async (days: number) => {
    setIsDeletingOldLogs(true);
    try {
      const { data } = await scrapingApi.deleteLogs({ older_than_days: days });
      await refetchLogs();
      setScrapingMessage({
        type: "success",
        text: data.message || `${data.deleted_count} logs supprimes`,
      });
      setTimeout(() => setScrapingMessage(null), 3000);
    } catch (error) {
      setScrapingMessage({
        type: "error",
        text: "Erreur lors de la suppression des logs",
      });
      setTimeout(() => setScrapingMessage(null), 5000);
    } finally {
      setIsDeletingOldLogs(false);
    }
  };

  const getLogStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-700";
      case "failed":
        return "bg-red-100 text-red-700";
      case "in_progress":
      case "started":
        return "bg-blue-100 text-blue-700";
      case "cancelled":
        return "bg-gray-100 text-gray-700";
      default:
        return "bg-gray-100 text-gray-500";
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return "-";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Show loading while checking auth - AFTER all hooks
  if (!isAuthenticated || !isAdmin) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verification des droits d&apos;acces...</p>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
      case "active":
      case "idle":
        return "text-green-500";
      case "running":
        return "text-blue-500";
      case "error":
        return "text-red-500";
      case "disabled":
        return "text-gray-400";
      default:
        return "text-gray-500";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
      case "active":
        return <CheckCircle size={16} className="text-green-500" />;
      case "running":
        return <RefreshCw size={16} className="text-blue-500 animate-spin" />;
      case "error":
        return <XCircle size={16} className="text-red-500" />;
      case "disabled":
        return <Pause size={16} className="text-gray-400" />;
      default:
        return <AlertTriangle size={16} className="text-yellow-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Admin Header */}
      <header className="bg-gray-900 text-white px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Shield className="text-red-400" size={28} />
            <div>
              <h1 className="text-xl font-bold">Administration FlipRadar</h1>
              <p className="text-gray-400 text-sm">Panneau de controle systeme</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <LiveDot isLive={status?.database === "connected"} label="Systeme" />

            {/* User info */}
            <div className="flex items-center gap-2 text-sm">
              <div className="w-8 h-8 rounded-full bg-red-600 flex items-center justify-center">
                {user?.email?.[0]?.toUpperCase() || "A"}
              </div>
              <div className="hidden md:block">
                <p className="font-medium">{user?.name || user?.email}</p>
                <p className="text-xs text-gray-400">{user?.plan}</p>
              </div>
            </div>

            <Link href="/dashboard">
              <Button variant="outline" size="sm" className="text-white border-gray-600 hover:bg-gray-800">
                Retour au dashboard
              </Button>
            </Link>

            <Button
              variant="outline"
              size="sm"
              className="text-red-400 border-red-600 hover:bg-red-900"
              onClick={handleLogout}
            >
              <LogOut size={16} className="mr-2" />
              Deconnexion
            </Button>
          </div>
        </div>
      </header>

      <div className="p-8 space-y-8">
        {/* System Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                  <Database size={20} className="text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Base de donnees</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(status?.database || "error")}
                    <span className={cn("font-medium", getStatusColor(status?.database || "error"))}>
                      {status?.database === "connected" ? "Connectee" : "Erreur"}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Activity size={20} className="text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Scraping</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(isRunningScrap ? "running" : status?.scraping || "idle")}
                    <span className={cn("font-medium", getStatusColor(isRunningScrap ? "running" : status?.scraping || "idle"))}>
                      {isRunningScrap ? "En cours..." : status?.scraping === "running" ? "En cours" : "Pret"}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <BarChart3 size={20} className="text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Deals</p>
                  <p className="text-xl font-bold text-gray-900">{status?.total_deals || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                  <Users size={20} className="text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Utilisateurs</p>
                  <p className="text-xl font-bold text-gray-900">{status?.total_users || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Scraping Control */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <RefreshCw size={20} className="text-blue-500" />
                  Controle du Scraping
                </CardTitle>
                <Button
                  onClick={() => handleRunScraping(selectedSources.length > 0 ? selectedSources : undefined)}
                  disabled={isRunningScrap}
                  className="gap-2"
                >
                  {isRunningScrap ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      En cours...
                    </>
                  ) : (
                    <>
                      <Play size={16} />
                      Lancer le scan
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Scraping message feedback */}
                {scrapingMessage && (
                  <div
                    className={cn(
                      "p-3 rounded-lg text-sm font-medium",
                      scrapingMessage.type === "success"
                        ? "bg-green-100 text-green-800 border border-green-200"
                        : "bg-red-100 text-red-800 border border-red-200"
                    )}
                  >
                    {scrapingMessage.type === "success" ? (
                      <CheckCircle size={16} className="inline mr-2" />
                    ) : (
                      <AlertTriangle size={16} className="inline mr-2" />
                    )}
                    {scrapingMessage.text}
                  </div>
                )}

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Dernier scan:</span>
                  <span className="font-medium">
                    {status?.last_scrape
                      ? new Date(status.last_scrape).toLocaleString("fr-FR")
                      : "Jamais"}
                  </span>
                </div>

                <div className="border-t pt-4">
                  <p className="text-sm font-medium text-gray-700 mb-3">Sources a scanner:</p>
                  <div className="space-y-2">
                    {sourcesLoading ? (
                      <div className="animate-pulse space-y-2">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="h-10 bg-gray-100 rounded-lg" />
                        ))}
                      </div>
                    ) : (
                      sources?.map((source) => {
                        const status = getSourceStatus(source);
                        const isPro = source.plan_required === "pro";
                        return (
                          <label
                            key={source.slug}
                            className={cn(
                              "flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors",
                              selectedSources.includes(source.slug)
                                ? "border-blue-500 bg-blue-50"
                                : isPro
                                ? "border-amber-300 hover:bg-amber-50"
                                : "border-gray-200 hover:bg-gray-50",
                              status === "disabled" && "opacity-50"
                            )}
                          >
                            <div className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                checked={selectedSources.includes(source.slug)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedSources([...selectedSources, source.slug]);
                                  } else {
                                    setSelectedSources(selectedSources.filter((s) => s !== source.slug));
                                  }
                                }}
                                disabled={status === "disabled"}
                                className="rounded border-gray-300 text-blue-600"
                              />
                              <div className="flex items-center gap-2">
                                {getStatusIcon(status)}
                                <span className="font-medium">{source.name}</span>
                                {isPro && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full">
                                    <Crown size={10} />
                                    PRO
                                  </span>
                                )}
                              </div>
                            </div>
                            <span className="text-sm text-gray-500">{source.total_deals_found} deals</span>
                          </label>
                        );
                      })
                    )}
                  </div>
                  {selectedSources.length > 0 && (
                    <p className="text-sm text-blue-600 mt-2">
                      {selectedSources.length} source(s) selectionnee(s)
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Webhook Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Webhook size={20} className="text-purple-500" />
                Configuration Discord
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Webhook Discord Global
                </label>
                <p className="text-xs text-gray-500 mb-2">
                  Les alertes seront envoyees sur ce canal Discord pour tous les utilisateurs
                </p>
                <Input
                  placeholder="https://discord.com/api/webhooks/..."
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                />
              </div>

              <div className="flex gap-2">
                <Button className="gap-2" disabled={!webhookUrl}>
                  <Save size={16} />
                  Enregistrer
                </Button>
                <Button variant="outline" className="gap-2" disabled={!webhookUrl}>
                  <Globe size={16} />
                  Tester le webhook
                </Button>
              </div>

              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Options d&apos;alertes</h4>
                <div className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="rounded border-gray-300 text-purple-600"
                    />
                    <span className="text-sm">Envoyer les alertes apres chaque scan</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      defaultChecked
                      className="rounded border-gray-300 text-purple-600"
                    />
                    <span className="text-sm">Inclure les deals avec score &gt; 70</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-purple-600"
                    />
                    <span className="text-sm">Envoyer un resume quotidien</span>
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Proxy Configuration */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Network size={20} className="text-cyan-500" />
                Configuration Proxy
              </CardTitle>
              <div className="flex items-center gap-2">
                {systemSettings?.use_rotating_proxy ? (
                  <span className="flex items-center gap-1.5 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                    <Zap size={12} />
                    Actif
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 text-gray-500 text-xs font-medium rounded-full">
                    Desactive
                  </span>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Mode Proxy Rotatif</p>
                <p className="text-sm text-gray-500">
                  Utiliser des proxies rotatifs pour eviter les blocages sur tous les scrapers (Vinted, Nike, Adidas, Zalando, etc.)
                </p>
              </div>
              <button
                onClick={handleToggleProxy}
                disabled={isTogglingProxy}
                className={cn(
                  "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                  systemSettings?.use_rotating_proxy ? "bg-green-500" : "bg-gray-300",
                  isTogglingProxy && "opacity-50 cursor-not-allowed"
                )}
              >
                <span
                  className={cn(
                    "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                    systemSettings?.use_rotating_proxy ? "translate-x-6" : "translate-x-1"
                  )}
                />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500 mb-1">Proxies charges</p>
                <p className="text-2xl font-bold text-gray-900">{systemSettings?.proxy_count || 0}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500 mb-1">Source</p>
                <p className="text-sm font-medium text-gray-900">Webshare.io</p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="gap-2"
                onClick={handleReloadProxies}
                disabled={isReloadingProxies || !systemSettings?.use_rotating_proxy}
              >
                {isReloadingProxies ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Rechargement...
                  </>
                ) : (
                  <>
                    <RefreshCw size={16} />
                    Recharger les proxies
                  </>
                )}
              </Button>
            </div>

            <div className="border-t pt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Informations</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Intervalle de scraping</span>
                  <span className="font-medium">{systemSettings?.scrape_interval_minutes || 15} min</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Scrapers simultanes max</span>
                  <span className="font-medium">{systemSettings?.max_concurrent_scrapers || 3}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Marge minimum</span>
                  <span className="font-medium">{systemSettings?.min_margin_percent || 20}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">FlipScore minimum</span>
                  <span className="font-medium">{systemSettings?.min_flip_score || 70}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sources Management */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Globe size={20} className="text-green-500" />
                Gestion des Sources
              </CardTitle>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-500">
                  {sources?.filter(s => s.plan_required !== "pro").length || 0} sources FREE
                </span>
                <span className="flex items-center gap-1 text-amber-600 font-medium">
                  <Crown size={14} />
                  {sources?.filter(s => s.plan_required === "pro").length || 0} sources PRO
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Source</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Plan</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Statut</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Deals</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Dernier scan</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sources?.map((source) => {
                    const status = getSourceStatus(source);
                    const isPro = source.plan_required === "pro";
                    return (
                      <tr key={source.slug} className={cn(
                        "border-b border-gray-100 hover:bg-gray-50",
                        isPro && "bg-amber-50/30"
                      )}>
                        <td className="py-3 px-4">
                          <span className="font-medium text-gray-900">{source.name}</span>
                        </td>
                        <td className="py-3 px-4">
                          {isPro ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full">
                              <Crown size={10} />
                              PRO
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                              FREE
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(status)}
                            <span className={cn("text-sm", getStatusColor(status))}>
                              {status === "active"
                                ? "Actif"
                                : status === "error"
                                ? "Erreur"
                                : "Desactive"}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-600">{source.total_deals_found}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-500">
                            {source.last_scraped_at
                              ? new Date(source.last_scraped_at).toLocaleString("fr-FR")
                              : "-"}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRunScraping([source.slug])}
                              disabled={status === "disabled" || isRunningScrap}
                            >
                              <Play size={14} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className={source.is_active ? "text-orange-500" : "text-green-500"}
                              onClick={() => handleToggleSource(source)}
                              title={source.is_active ? "Desactiver" : "Activer"}
                              disabled={updateSourceMutation.isPending}
                            >
                              {source.is_active ? <Pause size={14} /> : <Play size={14} />}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-gray-400 hover:text-gray-600"
                              onClick={() => handleOpenSourceSettings(source)}
                              title="Parametres"
                            >
                              <Settings size={14} />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Scraping Logs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText size={20} className="text-indigo-500" />
                Journal de Scraping
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchLogs()}
                  disabled={logsLoading}
                >
                  <RefreshCw size={14} className={cn(logsLoading && "animate-spin")} />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-orange-600 border-orange-300 hover:bg-orange-50"
                  onClick={() => handleDeleteOldLogs(7)}
                  disabled={isDeletingOldLogs}
                >
                  {isDeletingOldLogs ? (
                    <RefreshCw size={14} className="animate-spin mr-1" />
                  ) : (
                    <Trash2 size={14} className="mr-1" />
                  )}
                  Supprimer +7 jours
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {logsLoading && !logsData ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw size={24} className="animate-spin text-gray-400" />
              </div>
            ) : logsData?.logs && logsData.logs.length > 0 ? (
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 px-3 font-medium text-gray-500">Source</th>
                        <th className="text-left py-2 px-3 font-medium text-gray-500">Statut</th>
                        <th className="text-left py-2 px-3 font-medium text-gray-500">Debut</th>
                        <th className="text-left py-2 px-3 font-medium text-gray-500">Duree</th>
                        <th className="text-center py-2 px-3 font-medium text-gray-500">Deals</th>
                        <th className="text-center py-2 px-3 font-medium text-gray-500">Nouveaux</th>
                        <th className="text-center py-2 px-3 font-medium text-gray-500">Proxy</th>
                        <th className="text-right py-2 px-3 font-medium text-gray-500">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logsData.logs.map((log) => (
                        <tr key={log.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-2 px-3">
                            <span className="font-medium text-gray-900">{log.source_name}</span>
                            <span className="text-xs text-gray-400 ml-1">({log.triggered_by})</span>
                          </td>
                          <td className="py-2 px-3">
                            <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", getLogStatusColor(log.status))}>
                              {log.status === "completed" ? "Termine" :
                               log.status === "failed" ? "Echec" :
                               log.status === "in_progress" ? "En cours" :
                               log.status === "started" ? "Demarre" :
                               log.status === "cancelled" ? "Annule" : log.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-gray-600">
                            {new Date(log.started_at).toLocaleString("fr-FR", {
                              day: "2-digit",
                              month: "2-digit",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                          <td className="py-2 px-3 text-gray-600">
                            {formatDuration(log.duration_seconds)}
                          </td>
                          <td className="py-2 px-3 text-center">
                            <span className="font-medium text-gray-900">{log.deals_found}</span>
                          </td>
                          <td className="py-2 px-3 text-center">
                            {log.deals_new > 0 ? (
                              <span className="text-green-600 font-medium">+{log.deals_new}</span>
                            ) : (
                              <span className="text-gray-400">0</span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-center">
                            {log.proxy_used ? (
                              <Network size={14} className="text-green-500 mx-auto" />
                            ) : (
                              <span className="text-gray-300">-</span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-600 hover:bg-red-50"
                              onClick={() => handleDeleteLog(log.id)}
                              disabled={isDeletingLog === log.id}
                            >
                              {isDeletingLog === log.id ? (
                                <RefreshCw size={14} className="animate-spin" />
                              ) : (
                                <Trash2 size={14} />
                              )}
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {logsData.total > logsData.page_size && (
                  <div className="flex items-center justify-between pt-4 border-t">
                    <span className="text-sm text-gray-500">
                      Page {logsData.page} sur {Math.ceil(logsData.total / logsData.page_size)} ({logsData.total} logs)
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setLogsPage(logsPage - 1)}
                        disabled={logsPage <= 1}
                      >
                        <ChevronLeft size={14} />
                        Precedent
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setLogsPage(logsPage + 1)}
                        disabled={logsPage >= Math.ceil(logsData.total / logsData.page_size)}
                      >
                        Suivant
                        <ChevronRight size={14} />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <FileText size={32} className="mx-auto mb-2 text-gray-300" />
                <p>Aucun log de scraping pour le moment</p>
                <p className="text-xs mt-1">Les logs apparaitront ici apres le premier scraping</p>
              </div>
            )}

            {/* Error display for last failed logs */}
            {logsData?.logs.some(log => log.status === "failed" && log.error_message) && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg">
                <p className="text-sm font-medium text-red-800 mb-2">Dernieres erreurs:</p>
                {logsData.logs
                  .filter(log => log.status === "failed" && log.error_message)
                  .slice(0, 3)
                  .map(log => (
                    <div key={log.id} className="text-xs text-red-600 mb-1">
                      <span className="font-medium">{log.source_name}:</span> {log.error_message}
                    </div>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle size={20} />
              Zone Dangereuse
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
              <div>
                <p className="font-medium text-red-900">Purger les anciens deals</p>
                <p className="text-sm text-red-600">
                  Supprimer tous les deals de plus de 30 jours. Cette action est irreversible.
                </p>
              </div>
              <Button variant="outline" className="border-red-300 text-red-600 hover:bg-red-100">
                <Trash2 size={16} className="mr-2" />
                Purger
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Source Settings Modal */}
      {editingSource && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            {/* Modal Header */}
            <div className="bg-gray-900 text-white px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Settings size={20} className="text-gray-400" />
                  <div>
                    <h3 className="font-semibold">Parametres de {editingSource.name}</h3>
                    <p className="text-xs text-gray-400">{editingSource.base_url}</p>
                  </div>
                </div>
                <button
                  onClick={handleCloseSourceSettings}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <XCircle size={24} />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Status Toggle */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">Source active</p>
                  <p className="text-sm text-gray-500">Activer ou desactiver le scraping de cette source</p>
                </div>
                <button
                  onClick={() => setSourceSettings({ ...sourceSettings, is_active: !sourceSettings.is_active })}
                  className={cn(
                    "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                    sourceSettings.is_active ? "bg-green-500" : "bg-gray-300"
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                      sourceSettings.is_active ? "translate-x-6" : "translate-x-1"
                    )}
                  />
                </button>
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priorite de scraping
                </label>
                <p className="text-xs text-gray-500 mb-3">
                  Les sources avec une priorite elevee sont scrapees en premier (1 = haute, 10 = basse)
                </p>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min={1}
                    max={10}
                    value={sourceSettings.priority}
                    onChange={(e) => setSourceSettings({ ...sourceSettings, priority: Number(e.target.value) })}
                    className="flex-1"
                  />
                  <span className="w-8 text-center font-bold text-gray-900">{sourceSettings.priority}</span>
                </div>
              </div>

              {/* Source Info */}
              <div className="border-t pt-4 space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Informations</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-gray-500">Slug:</div>
                  <div className="font-mono text-gray-900">{editingSource.slug}</div>
                  <div className="text-gray-500">Deals trouves:</div>
                  <div className="font-medium text-gray-900">{editingSource.total_deals_found}</div>
                  <div className="text-gray-500">Dernier scan:</div>
                  <div className="text-gray-900">
                    {editingSource.last_scraped_at
                      ? new Date(editingSource.last_scraped_at).toLocaleString("fr-FR")
                      : "Jamais"}
                  </div>
                  {editingSource.last_error && (
                    <>
                      <div className="text-red-500">Derniere erreur:</div>
                      <div className="text-red-600 text-xs">{editingSource.last_error}</div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3">
              <Button variant="outline" onClick={handleCloseSourceSettings} disabled={updateSourceMutation.isPending}>
                Annuler
              </Button>
              <Button onClick={handleSaveSourceSettings} className="gap-2" disabled={updateSourceMutation.isPending}>
                {updateSourceMutation.isPending ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Enregistrement...
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    Enregistrer
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
