"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface ScoreDistribution {
  range_label: string;
  count: number;
  percentage: number;
}

interface FlipScoreChartProps {
  data: ScoreDistribution[];
}

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#10b981"];

export function FlipScoreChart({ data }: FlipScoreChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          fill="#8884d8"
          paddingAngle={2}
          dataKey="count"
          nameKey="range_label"
          label={({ range_label, percentage }) =>
            percentage > 5 ? `${percentage.toFixed(0)}%` : ""
          }
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value, name) => [`${value} deals`, name]}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
