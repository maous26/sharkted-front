"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FlipScoreChart } from "@/components/charts/flip-score-chart";
import { TrendsChart } from "@/components/charts/trends-chart";
import { analyticsApi } from "@/lib/api";

export default function AnalyticsPage() {
  // Fetch score distribution
  const { data: scoreDistribution } = useQuery({
    queryKey: ["analytics", "score-distribution"],
    queryFn: async () => {
      const { data } = await analyticsApi.scoreDistribution();
      return data;
    },
  });

  // Fetch deals trend
  const { data: dealsTrend } = useQuery({
    queryKey: ["analytics", "trends", "deals"],
    queryFn: async () => {
      const { data } = await analyticsApi.dealsTrend(30);
      return data;
    },
  });

  // Fetch brands stats
  const { data: brandStats } = useQuery({
    queryKey: ["analytics", "brands"],
    queryFn: async () => {
      const { data } = await analyticsApi.brands(10);
      return data;
    },
  });

  // Fetch categories stats
  const { data: categoryStats } = useQuery({
    queryKey: ["analytics", "categories"],
    queryFn: async () => {
      const { data } = await analyticsApi.categories();
      return data;
    },
  });

  return (
    <div>
      <Header
        title="Analytics"
        subtitle="Analysez vos performances et le marché"
      />

      <div className="p-8">
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Score Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Distribution des FlipScores</CardTitle>
            </CardHeader>
            <CardContent>
              <FlipScoreChart data={scoreDistribution || []} />
            </CardContent>
          </Card>

          {/* Deals Trend */}
          <Card>
            <CardHeader>
              <CardTitle>Deals par jour (30 derniers jours)</CardTitle>
            </CardHeader>
            <CardContent>
              <TrendsChart
                data={dealsTrend?.data || []}
                color="#22c55e"
                yAxisLabel="Deals"
              />
            </CardContent>
          </Card>
        </div>

        {/* Tables Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Brands Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Top Marques</CardTitle>
            </CardHeader>
            <CardContent>
              {!brandStats || brandStats.length === 0 ? (
                <div className="text-center text-gray-400 py-8">Aucune donnee disponible</div>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-2">Marque</th>
                      <th className="pb-2">Deals</th>
                      <th className="pb-2">Score moy.</th>
                      <th className="pb-2">Marge moy.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {brandStats.map((brand: any, i: number) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-3 font-medium">{brand.brand}</td>
                        <td className="py-3">{brand.deal_count}</td>
                        <td className="py-3">{(brand.avg_flip_score || 0).toFixed(1)}</td>
                        <td className="py-3 text-green-600">
                          +{(brand.avg_margin_pct || 0).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>

          {/* Categories Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Par Categorie</CardTitle>
            </CardHeader>
            <CardContent>
              {!categoryStats || categoryStats.length === 0 ? (
                <div className="text-center text-gray-400 py-8">Aucune donnee disponible</div>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-2">Categorie</th>
                      <th className="pb-2">Deals</th>
                      <th className="pb-2">Score moy.</th>
                      <th className="pb-2">Marge moy.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryStats.map((cat: any, i: number) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-3 font-medium capitalize">{cat.category}</td>
                        <td className="py-3">{cat.deal_count}</td>
                        <td className="py-3">{(cat.avg_flip_score || 0).toFixed(1)}</td>
                        <td className="py-3 text-green-600">
                          +{(cat.avg_margin_pct || 0).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
