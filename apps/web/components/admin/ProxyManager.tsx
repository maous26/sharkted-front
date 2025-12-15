"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw,
  Plus,
  Trash2,
  Save,
  TestTube,
  CheckCircle,
  XCircle,
  Globe,
  DollarSign,
  Activity,
  Settings,
  Eye,
  EyeOff,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { adminApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Proxy {
  id: number;
  name: string;
  provider: string;
  proxy_type: string;
  host: string;
  port: number;
  username: string;
  password: string;
  country: string;
  zone?: string;
  enabled: boolean;
  is_default: boolean;
  success_count: number;
  error_count: number;
  success_rate: number;
  last_used_at?: string;
}

interface ProxyCosts {
  period_days: number;
  total_requests: number;
  total_cost_eur: number;
  success_rate: number;
  avg_cost_per_request: number;
  by_trigger: Record<string, { count: number; cost: number }>;
  by_site: Record<string, { count: number; cost: number }>;
  premium_users_active: number;
  projected_monthly_cost: number;
}

export function ProxyManager() {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [showPasswords, setShowPasswords] = useState<Record<number, boolean>>({});
  const [testingProxy, setTestingProxy] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<{ id: number; success: boolean; message: string } | null>(null);

  const [formData, setFormData] = useState({
    name: "BrightData Web Unlocker",
    provider: "brightdata",
    proxy_type: "web_unlocker",
    host: "brd.superproxy.io",
    port: 33335,
    username: "",
    password: "",
    country: "FR",
    zone: "web_unlocker1",
    enabled: true,
    is_default: true,
  });

  const { data: proxiesData, isLoading: proxiesLoading } = useQuery({
    queryKey: ["admin", "proxies"],
    queryFn: async () => {
      const { data } = await adminApi.proxies();
      return data;
    },
  });

  const { data: costsData } = useQuery<ProxyCosts>({
    queryKey: ["admin", "proxy-costs"],
    queryFn: async () => {
      const { data } = await adminApi.proxyCosts(7);
      return data;
    },
    refetchInterval: 60000,
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      return adminApi.createProxy(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "proxies"] });
      setShowAddForm(false);
      setFormData({
        name: "BrightData Web Unlocker",
        provider: "brightdata",
        proxy_type: "web_unlocker",
        host: "brd.superproxy.io",
        port: 33335,
        username: "",
        password: "",
        country: "FR",
        zone: "web_unlocker1",
        enabled: true,
        is_default: true,
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return adminApi.deleteProxy(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "proxies"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, enabled }: { id: number; enabled: boolean }) => {
      return adminApi.updateProxy(id, { enabled });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "proxies"] });
    },
  });

  const handleTestProxy = async (id: number) => {
    setTestingProxy(id);
    setTestResult(null);
    try {
      const { data } = await adminApi.testProxy(id);
      setTestResult({
        id,
        success: data.status === "success",
        message: data.status === "success"
          ? `OK (${data.duration_ms}ms)`
          : data.error || "Erreur inconnue",
      });
    } catch {
      setTestResult({
        id,
        success: false,
        message: "Erreur de connexion",
      });
    }
    setTestingProxy(null);
  };

  const proxies: Proxy[] = proxiesData?.proxies || [];

  return (
    <div className="space-y-6">
      {costsData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Activity size={20} className="text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Requetes (7j)</p>
                  <p className="text-xl font-bold">{costsData.total_requests}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <DollarSign size={20} className="text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Cout (7j)</p>
                  <p className="text-xl font-bold">{costsData.total_cost_eur.toFixed(2)} EUR</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Globe size={20} className="text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Premium actifs</p>
                  <p className="text-xl font-bold">{costsData.premium_users_active}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <DollarSign size={20} className="text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Projection/mois</p>
                  <p className="text-xl font-bold">{costsData.projected_monthly_cost.toFixed(2)} EUR</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Settings size={20} />
            Configuration des Proxies
          </CardTitle>
          <Button onClick={() => setShowAddForm(true)} className="gap-2">
            <Plus size={16} />
            Ajouter un Proxy
          </Button>
        </CardHeader>
        <CardContent>
          {proxiesLoading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="animate-spin text-gray-400" />
            </div>
          ) : proxies.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Globe size={48} className="mx-auto mb-4 opacity-50" />
              <p>Aucun proxy configure</p>
              <p className="text-sm">Ajoutez vos credentials BrightData pour activer le scraping premium</p>
            </div>
          ) : (
            <div className="space-y-4">
              {proxies.map((proxy) => (
                <div
                  key={proxy.id}
                  className={cn(
                    "border rounded-lg p-4",
                    proxy.enabled ? "border-green-200 bg-green-50/30" : "border-gray-200 bg-gray-50"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{proxy.name}</h3>
                        {proxy.is_default && (
                          <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                            Par defaut
                          </span>
                        )}
                        {proxy.enabled ? (
                          <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded flex items-center gap-1">
                            <CheckCircle size={12} /> Actif
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded flex items-center gap-1">
                            <XCircle size={12} /> Inactif
                          </span>
                        )}
                      </div>

                      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Type:</span>
                          <span className="ml-2 font-mono">{proxy.proxy_type}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Host:</span>
                          <span className="ml-2 font-mono">{proxy.host}:{proxy.port}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">User:</span>
                          <span className="ml-2 font-mono text-xs">{proxy.username.slice(0, 30)}...</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Pass:</span>
                          <span className="ml-2 font-mono">
                            {showPasswords[proxy.id] ? proxy.password : "********"}
                          </span>
                          <button
                            onClick={() => setShowPasswords({ ...showPasswords, [proxy.id]: !showPasswords[proxy.id] })}
                            className="ml-1 text-gray-400 hover:text-gray-600"
                          >
                            {showPasswords[proxy.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                          </button>
                        </div>
                      </div>

                      <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                        <span>Succes: {proxy.success_count}</span>
                        <span>Erreurs: {proxy.error_count}</span>
                        <span>Taux: {proxy.success_rate}%</span>
                        {proxy.last_used_at && (
                          <span>Dernier usage: {new Date(proxy.last_used_at).toLocaleString("fr-FR")}</span>
                        )}
                      </div>

                      {testResult?.id === proxy.id && (
                        <div className={cn(
                          "mt-2 p-2 rounded text-sm",
                          testResult.success ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        )}>
                          {testResult.success ? "Test reussi" : "Test echoue"}: {testResult.message}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTestProxy(proxy.id)}
                        disabled={testingProxy === proxy.id}
                      >
                        {testingProxy === proxy.id ? (
                          <RefreshCw size={14} className="animate-spin" />
                        ) : (
                          <TestTube size={14} />
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleMutation.mutate({ id: proxy.id, enabled: !proxy.enabled })}
                      >
                        {proxy.enabled ? "Desactiver" : "Activer"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => {
                          if (confirm("Supprimer ce proxy ?")) {
                            deleteMutation.mutate(proxy.id);
                          }
                        }}
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold">Ajouter un Proxy BrightData</h2>
              <p className="text-sm text-gray-500 mt-1">
                Entrez vos credentials Web Unlocker
              </p>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nom</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="BrightData Web Unlocker"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Host</label>
                  <Input
                    value={formData.host}
                    onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                    placeholder="brd.superproxy.io"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Port</label>
                  <Input
                    type="number"
                    value={formData.port}
                    onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                    placeholder="33335"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Username</label>
                <Input
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="brd-customer-xxx-zone-web_unlocker1"
                  className="font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Format: brd-customer-CUSTOMER_ID-zone-ZONE_NAME
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Password</label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Votre mot de passe BrightData"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Type</label>
                  <select
                    value={formData.proxy_type}
                    onChange={(e) => setFormData({ ...formData, proxy_type: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="web_unlocker">Web Unlocker</option>
                    <option value="residential">Residential</option>
                    <option value="datacenter">Datacenter</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Pays</label>
                  <Input
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    placeholder="FR"
                  />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  />
                  <span className="text-sm">Activer</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  />
                  <span className="text-sm">Par defaut</span>
                </label>
              </div>
            </div>

            <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
              <Button variant="outline" onClick={() => setShowAddForm(false)}>
                Annuler
              </Button>
              <Button
                onClick={() => createMutation.mutate(formData)}
                disabled={createMutation.isPending || !formData.username || !formData.password}
                className="gap-2"
              >
                {createMutation.isPending ? (
                  <RefreshCw size={16} className="animate-spin" />
                ) : (
                  <Save size={16} />
                )}
                Enregistrer
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
