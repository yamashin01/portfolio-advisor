"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import type { MarketSummaryResponse } from "@/types/api";
import type { AssetResponse } from "@/types/asset";

export default function MarketPage() {
  const [summary, setSummary] = useState<MarketSummaryResponse | null>(null);
  const [assets, setAssets] = useState<AssetResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiClient.getMarketSummary().catch(() => null),
      apiClient.getAssets({ per_page: 50 }).catch(() => null),
    ]).then(([summaryRes, assetsRes]) => {
      if (summaryRes) setSummary(summaryRes);
      if (assetsRes) setAssets(assetsRes.items);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-muted-foreground">読み込み中...</p>
      </div>
    );
  }

  const marketLabel: Record<string, string> = { us: "米国", jp: "日本" };
  const typeLabel: Record<string, string> = { etf: "ETF", bond: "債券", reit: "REIT" };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">マーケット情報</h1>

      {/* Market Summary */}
      {summary && (
        <section className="mb-8">
          <h2 className="mb-4 text-lg font-semibold">マーケット概要</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {summary.indices.map((idx) => (
              <Card key={idx.symbol}>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">{idx.name}</p>
                  <p className="text-xl font-bold">
                    {idx.value?.toLocaleString() ?? "—"}
                  </p>
                  {idx.change_pct !== null && (
                    <p
                      className={`text-sm ${
                        idx.change_pct >= 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {idx.change_pct >= 0 ? "+" : ""}
                      {(idx.change_pct * 100).toFixed(2)}%
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
            {summary.forex.map((fx) => (
              <Card key={fx.pair}>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">{fx.pair}</p>
                  <p className="text-xl font-bold">
                    {fx.rate?.toFixed(2) ?? "—"}
                  </p>
                  {fx.change_pct !== null && (
                    <p
                      className={`text-sm ${
                        (fx.change_pct ?? 0) >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {(fx.change_pct ?? 0) >= 0 ? "+" : ""}
                      {((fx.change_pct ?? 0) * 100).toFixed(2)}%
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Asset List */}
      <section>
        <h2 className="mb-4 text-lg font-semibold">対象銘柄一覧</h2>
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left">シンボル</th>
                <th className="px-4 py-2 text-left">銘柄名</th>
                <th className="px-4 py-2 text-left">種別</th>
                <th className="px-4 py-2 text-left">市場</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.symbol} className="border-b">
                  <td className="px-4 py-2 font-mono">{asset.symbol}</td>
                  <td className="px-4 py-2">{asset.name_ja || asset.symbol}</td>
                  <td className="px-4 py-2">
                    <Badge variant="secondary">
                      {typeLabel[asset.asset_type] || asset.asset_type}
                    </Badge>
                  </td>
                  <td className="px-4 py-2">
                    <Badge variant="outline">
                      {marketLabel[asset.market] || asset.market}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
