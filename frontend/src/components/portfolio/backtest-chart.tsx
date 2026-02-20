"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { BenchmarkResult, TimeSeriesPoint } from "@/types/portfolio";

interface BacktestChartProps {
  timeSeries: TimeSeriesPoint[];
  benchmarks?: Record<string, BenchmarkResult> | null;
}

interface ChartDataItem {
  date: string;
  dateLabel: string;
  value: number;
  returnPct: number;
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
      <p className="text-xs text-muted-foreground">{data.dateLabel}</p>
      <p className="mt-1 text-sm font-semibold text-card-foreground">
        {`評価額: ${data.value.toLocaleString("ja-JP", { maximumFractionDigits: 0 })} 円`}
      </p>
      <p
        className="text-sm"
        style={{
          color:
            data.returnPct >= 0
              ? "oklch(0.60 0.18 145)"
              : "oklch(0.60 0.22 25)",
        }}
      >
        {`リターン: ${data.returnPct >= 0 ? "+" : ""}${(data.returnPct * 100).toFixed(2)}%`}
      </p>
    </div>
  );
}

function formatYAxis(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toString();
}

export function BacktestChart({ timeSeries, benchmarks }: BacktestChartProps) {
  if (timeSeries.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        バックテストデータがありません
      </div>
    );
  }

  const chartData: ChartDataItem[] = timeSeries.map((point) => {
    const d = new Date(point.date);
    return {
      date: point.date,
      dateLabel: `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`,
      value: Math.round(point.value),
      returnPct: point.return_pct,
    };
  });

  const tickInterval = Math.max(1, Math.floor(chartData.length / 6));

  return (
    <div className="space-y-3">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart
          data={chartData}
          margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="oklch(0.8 0 0 / 40%)"
            vertical={false}
          />
          <XAxis
            dataKey="dateLabel"
            tick={{ fontSize: 11, fill: "oklch(0.556 0 0)" }}
            tickLine={false}
            axisLine={false}
            interval={tickInterval}
          />
          <YAxis
            tickFormatter={formatYAxis}
            tick={{ fontSize: 11, fill: "oklch(0.556 0 0)" }}
            tickLine={false}
            axisLine={false}
            width={52}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="oklch(0.55 0.20 255)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: "oklch(0.55 0.20 255)" }}
          />
        </LineChart>
      </ResponsiveContainer>

      {benchmarks && Object.keys(benchmarks).length > 0 && (
        <div className="flex flex-wrap gap-4 px-2">
          {Object.entries(benchmarks).map(([name, bm]) => (
            <div
              key={name}
              className="rounded-md border bg-muted/50 px-3 py-1.5 text-xs"
            >
              <span className="font-medium">{name}</span>
              <span className="ml-2 text-muted-foreground">
                リターン:{" "}
                <span className="tabular-nums">
                  {(bm.total_return * 100).toFixed(1)}%
                </span>
              </span>
              <span className="ml-2 text-muted-foreground">
                CAGR:{" "}
                <span className="tabular-nums">
                  {(bm.cagr * 100).toFixed(1)}%
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
