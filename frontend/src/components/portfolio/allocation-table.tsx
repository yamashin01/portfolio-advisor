"use client";

import { Badge } from "@/components/ui/badge";
import type { AllocationResponse } from "@/types/portfolio";

const ASSET_TYPE_LABELS: Record<string, string> = {
  etf: "ETF",
  bond: "債券",
  reit: "REIT",
};

const MARKET_LABELS: Record<string, string> = {
  us: "米国",
  jp: "日本",
};

interface AllocationTableProps {
  allocations: AllocationResponse[];
  currency: string;
}

export function AllocationTable({ allocations, currency }: AllocationTableProps) {
  if (allocations.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        配分データがありません
      </p>
    );
  }

  const currencyLabel = currency === "JPY" ? "円" : currency;

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="whitespace-nowrap px-3 py-2 font-medium">
              シンボル
            </th>
            <th className="whitespace-nowrap px-3 py-2 font-medium">銘柄名</th>
            <th className="whitespace-nowrap px-3 py-2 font-medium">種別</th>
            <th className="whitespace-nowrap px-3 py-2 font-medium">市場</th>
            <th className="whitespace-nowrap px-3 py-2 text-right font-medium">
              比率
            </th>
            <th className="whitespace-nowrap px-3 py-2 text-right font-medium">
              金額 ({currencyLabel})
            </th>
          </tr>
        </thead>
        <tbody>
          {allocations.map((allocation) => {
            const { asset, weight, amount } = allocation;
            const assetTypeLabel =
              ASSET_TYPE_LABELS[asset.asset_type] ?? asset.asset_type;
            const marketLabel =
              MARKET_LABELS[asset.market] ?? asset.market;
            const weightPct = (weight * 100).toFixed(1);

            return (
              <tr
                key={asset.symbol}
                className="border-b transition-colors hover:bg-muted/50"
              >
                <td className="whitespace-nowrap px-3 py-2.5 font-mono text-sm font-semibold">
                  {asset.symbol}
                </td>
                <td className="px-3 py-2.5">
                  {asset.name_ja ?? asset.symbol}
                </td>
                <td className="px-3 py-2.5">
                  <Badge variant="secondary">{assetTypeLabel}</Badge>
                </td>
                <td className="px-3 py-2.5">
                  <Badge variant="outline">{marketLabel}</Badge>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-right tabular-nums">
                  {weightPct}%
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-right tabular-nums">
                  {amount != null ? amount.toLocaleString("ja-JP") : "-"}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="border-t font-semibold">
            <td className="px-3 py-2.5" colSpan={4}>
              合計
            </td>
            <td className="whitespace-nowrap px-3 py-2.5 text-right tabular-nums">
              {(
                allocations.reduce((sum, a) => sum + a.weight, 0) * 100
              ).toFixed(1)}
              %
            </td>
            <td className="whitespace-nowrap px-3 py-2.5 text-right tabular-nums">
              {allocations.some((a) => a.amount != null)
                ? allocations
                    .reduce((sum, a) => sum + (a.amount ?? 0), 0)
                    .toLocaleString("ja-JP")
                : "-"}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
