"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import type { AnnualReturn } from "@/types/portfolio";

const COLOR_POSITIVE = "oklch(0.60 0.18 145)";
const COLOR_NEGATIVE = "oklch(0.60 0.22 25)";

interface PerformanceChartProps {
  annualReturns: AnnualReturn[];
}

interface ChartDataItem {
  year: string;
  returnPct: number;
  displayValue: string;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDataItem }>;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;
  const isPositive = data.returnPct >= 0;

  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-md">
      <p className="text-xs text-muted-foreground">{data.year}年</p>
      <p
        className="mt-1 text-sm font-semibold"
        style={{ color: isPositive ? COLOR_POSITIVE : COLOR_NEGATIVE }}
      >
        {`${isPositive ? "+" : ""}${data.displayValue}`}
      </p>
    </div>
  );
}

export function PerformanceChart({ annualReturns }: PerformanceChartProps) {
  if (annualReturns.length === 0) {
    return (
      <div className="flex h-[280px] items-center justify-center text-muted-foreground">
        年次リターンデータがありません
      </div>
    );
  }

  const chartData: ChartDataItem[] = annualReturns.map((ar) => ({
    year: String(ar.year),
    returnPct: Math.round(ar.return_pct * 10000) / 100,
    displayValue: `${(ar.return_pct * 100).toFixed(1)}%`,
  }));

  const maxAbs = Math.max(
    ...chartData.map((d) => Math.abs(d.returnPct)),
    1,
  );
  const domainBound = Math.ceil(maxAbs / 5) * 5;

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={chartData}
        margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="oklch(0.8 0 0 / 40%)"
          vertical={false}
        />
        <XAxis
          dataKey="year"
          tick={{ fontSize: 12, fill: "oklch(0.556 0 0)" }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tickFormatter={(v: number) => `${v}%`}
          tick={{ fontSize: 11, fill: "oklch(0.556 0 0)" }}
          tickLine={false}
          axisLine={false}
          width={48}
          domain={[-domainBound, domainBound]}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "oklch(0.9 0 0 / 30%)" }} />
        <Bar dataKey="returnPct" radius={[4, 4, 0, 0]} maxBarSize={48}>
          {chartData.map((entry, index) => (
            <Cell
              key={`bar-${index}`}
              fill={entry.returnPct >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
