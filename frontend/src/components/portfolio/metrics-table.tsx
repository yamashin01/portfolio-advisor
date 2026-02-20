"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { PortfolioMetrics } from "@/types/portfolio";

const STRATEGY_LABELS: Record<string, string> = {
  min_volatility: "安定重視",
  hrp: "バランス型",
  max_sharpe: "積極型",
  risk_parity: "リスクパリティ",
  equal_weight: "均等配分",
};

interface MetricsTableProps {
  metrics: PortfolioMetrics;
  strategy: string;
}

function formatPercent(value: number | null): string {
  if (value == null) return "-";
  return `${(value * 100).toFixed(2)}%`;
}

function formatRatio(value: number | null): string {
  if (value == null) return "-";
  return value.toFixed(2);
}

export function MetricsTable({ metrics, strategy }: MetricsTableProps) {
  const strategyLabel = STRATEGY_LABELS[strategy] ?? strategy;

  const items = [
    {
      label: "戦略",
      value: strategyLabel,
      description: "最適化手法",
    },
    {
      label: "期待リターン",
      value: formatPercent(metrics.expected_return),
      description: "年率",
    },
    {
      label: "ボラティリティ",
      value: formatPercent(metrics.volatility),
      description: "年率",
    },
    {
      label: "シャープレシオ",
      value: formatRatio(metrics.sharpe_ratio),
      description: "リスク調整後リターン",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">ポートフォリオ指標</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {items.map((item) => (
            <div key={item.label} className="space-y-1">
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="text-lg font-semibold tabular-nums">
                {item.value}
              </p>
              <p className="text-xs text-muted-foreground">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
