"use client";

import { useQuery } from "@tanstack/react-query";
import { Bell, CheckCircle, ExternalLink, MousePointer } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { alertsApi } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

export default function AlertsPage() {
  // Fetch alerts
  const { data: alertsData, isLoading } = useQuery({
    queryKey: ["alerts"],
    queryFn: async () => {
      const { data } = await alertsApi.list({ per_page: 50 });
      return data;
    },
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ["alerts", "stats"],
    queryFn: async () => {
      const { data } = await alertsApi.stats(30);
      return data;
    },
  });

  return (
    <div>
      <Header
        title="Alertes"
        subtitle="Historique de vos alertes Discord et email"
      />

      <div className="p-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Bell className="text-blue-600" size={20} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_sent || 0}</p>
                  <p className="text-sm text-gray-500">Alertes envoyées</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                  <MousePointer className="text-green-600" size={20} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_clicked || 0}</p>
                  <p className="text-sm text-gray-500">Clics</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <CheckCircle className="text-purple-600" size={20} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_purchased || 0}</p>
                  <p className="text-sm text-gray-500">Achats</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                  <ExternalLink className="text-orange-600" size={20} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.click_rate?.toFixed(1) || 0}%</p>
                  <p className="text-sm text-gray-500">Taux de clic</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts List */}
        <Card>
          <CardHeader>
            <CardTitle>Alertes récentes</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : alertsData?.items?.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Aucune alerte envoyée pour le moment.
                <br />
                Configurez votre webhook Discord dans les paramètres.
              </div>
            ) : (
              <div className="space-y-3">
                {alertsData?.items?.map((alert: any) => (
                  <div
                    key={alert.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          alert.status === "sent" ? "bg-green-500" : "bg-gray-400"
                        }`}
                      />
                      <div>
                        <p className="font-medium">
                          {alert.alert_data?.product_name || "Deal"}
                        </p>
                        <p className="text-sm text-gray-500">
                          Score: {alert.alert_data?.flip_score || 0}/100 • Marge:{" "}
                          {alert.alert_data?.margin_pct?.toFixed(0) || 0}%
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={alert.channel === "discord" ? "info" : "default"}>
                        {alert.channel}
                      </Badge>
                      {alert.was_clicked && (
                        <Badge variant="success">Cliqué</Badge>
                      )}
                      {alert.led_to_purchase && (
                        <Badge variant="success">Acheté</Badge>
                      )}
                      <span className="text-sm text-gray-400">
                        {timeAgo(alert.sent_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
