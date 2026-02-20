"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { AllocationResponse } from "@/types/portfolio";

const COLORS = [
  "oklch(0.65 0.20 250)",   // blue
  "oklch(0.70 0.18 160)",   // teal
  "oklch(0.75 0.16 80)",    // amber
  "oklch(0.60 0.22 300)",   // purple
  "oklch(0.65 0.22 25)",    // coral
  "oklch(0.72 0.15 200)",   // cyan
  "oklch(0.68 0.20 340)",   // pink
  "oklch(0.78 0.14 110)",   // lime
  "oklch(0.58 0.18 270)",   // indigo
  "oklch(0.74 0.16 50)",    // orange
];

interface AllocationChartProps {
  allocations: AllocationResponse[];
  size?: "sm" | "lg";
}

interface ChartDataItem {
  name: string;
  symbol: string;
  value: number;
  amount: number | null;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDataItem; color: string }>;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;

  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-md">
      <p className="text-sm font-semibold text-card-foreground">
        {data.name}
      </p>
      <p className="text-xs text-muted-foreground">{data.symbol}</p>
      <p className="mt-1 text-sm" style={{ color: payload[0].color }}>
        {`比率: ${data.value.toFixed(1)}%`}
      </p>
      {data.amount != null && (
        <p className="text-sm text-card-foreground">
          {`金額: ${data.amount.toLocaleString("ja-JP")} 円`}
        </p>
      )}
    </div>
  );
}

export function AllocationChart({ allocations, size = "lg" }: AllocationChartProps) {
  const chartData: ChartDataItem[] = allocations.map((a) => ({
    name: a.asset.name_ja ?? a.asset.symbol,
    symbol: a.asset.symbol,
    value: Math.round(a.weight * 1000) / 10,
    amount: a.amount,
  }));

  const containerHeight = size === "sm" ? 240 : 380;
  const outerRadius = size === "sm" ? 80 : 140;
  const innerRadius = size === "sm" ? 45 : 80;

  if (allocations.length === 0) {
    return (
      <div className="flex items-center justify-center text-muted-foreground" style={{ height: containerHeight }}>
        配分データがありません
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={containerHeight}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          outerRadius={outerRadius}
          innerRadius={innerRadius}
          dataKey="value"
          nameKey="name"
          paddingAngle={2}
        >
          {chartData.map((_, index) => (
            <Cell
              key={`cell-${index}`}
              fill={COLORS[index % COLORS.length]}
              strokeWidth={1}
              stroke="oklch(1 0 0 / 30%)"
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        {size === "lg" && (
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            iconSize={10}
            formatter={(value: string) => (
              <span className="text-xs text-card-foreground">{value}</span>
            )}
          />
        )}
      </PieChart>
    </ResponsiveContainer>
  );
}
