"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AllocationTable } from "@/components/portfolio/allocation-table";
import { MetricsTable } from "@/components/portfolio/metrics-table";
import { usePortfolioResultStore } from "@/stores/portfolio-result-store";
import { apiClient } from "@/lib/api-client";

const AllocationChart = dynamic(
  () =>
    import("@/components/portfolio/allocation-chart").then(
      (m) => m.AllocationChart
    ),
  { ssr: false, loading: () => <div className="h-64 animate-pulse rounded bg-muted" /> }
);

const BacktestChart = dynamic(
  () =>
    import("@/components/portfolio/backtest-chart").then(
      (m) => m.BacktestChart
    ),
  { ssr: false, loading: () => <div className="h-64 animate-pulse rounded bg-muted" /> }
);

const PerformanceChart = dynamic(
  () =>
    import("@/components/portfolio/performance-chart").then(
      (m) => m.PerformanceChart
    ),
  { ssr: false, loading: () => <div className="h-64 animate-pulse rounded bg-muted" /> }
);

export default function PortfolioPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[50vh] items-center justify-center">
          <p className="text-muted-foreground">読み込み中...</p>
        </div>
      }
    >
      <PortfolioContent />
    </Suspense>
  );
}

function PortfolioContent() {
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [explainLoading, setExplainLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { portfolio, backtest, explanation, setPortfolio, setBacktest, setExplanation } =
    usePortfolioResultStore();

  useEffect(() => {
    const riskScore = searchParams.get("risk_score");
    const riskTolerance = searchParams.get("risk_tolerance");
    const investmentHorizon = searchParams.get("investment_horizon");
    const strategy = searchParams.get("strategy");

    if (!riskScore || !riskTolerance || !investmentHorizon) {
      if (!portfolio) {
        setError("リスク診断結果がありません。先にリスク診断を行ってください。");
      }
      return;
    }

    setLoading(true);
    setError(null);

    apiClient
      .generatePortfolio({
        risk_score: Number(riskScore),
        risk_tolerance: riskTolerance,
        investment_horizon: investmentHorizon,
        strategy: strategy || "auto",
        investment_amount: 1000000,
        currency: "JPY",
      })
      .then((result) => {
        setPortfolio(result);
        // Auto-trigger backtest
        runBacktest(result.allocations);
      })
      .catch(() => setError("ポートフォリオの生成に失敗しました。"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const runBacktest = async (
    allocations: { asset: { symbol: string }; weight: number }[]
  ) => {
    setBacktestLoading(true);
    try {
      const result = await apiClient.runBacktest({
        allocations: allocations.map((a) => ({
          symbol: a.asset.symbol,
          weight: a.weight,
        })),
        period_years: 5,
        initial_investment: 1000000,
      });
      setBacktest(result);
    } catch {
      // Backtest failure is non-critical
    } finally {
      setBacktestLoading(false);
    }
  };

  const handleExplain = async () => {
    if (!portfolio) return;
    setExplainLoading(true);
    try {
      const result = await apiClient.explainPortfolio({
        strategy: portfolio.strategy,
        risk_tolerance: portfolio.risk_profile.risk_tolerance,
        allocations: portfolio.allocations.map((a) => ({
          symbol: a.asset.symbol,
          name_ja: a.asset.name_ja || undefined,
          weight: a.weight,
        })),
        metrics: portfolio.metrics.expected_return !== null
          ? {
              expected_return: portfolio.metrics.expected_return!,
              volatility: portfolio.metrics.volatility!,
              sharpe_ratio: portfolio.metrics.sharpe_ratio!,
            }
          : undefined,
      });
      setExplanation(result.explanation);
    } catch {
      setExplanation("説明の生成に失敗しました。");
    } finally {
      setExplainLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-muted-foreground">ポートフォリオを生成中...</p>
      </div>
    );
  }

  if (error && !portfolio) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error}</p>
        <Button asChild>
          <Link href="/risk-assessment">リスク診断を始める</Link>
        </Button>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">
          ポートフォリオがありません。
        </p>
        <Button asChild>
          <Link href="/risk-assessment">リスク診断を始める</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{portfolio.name || "ポートフォリオ"}</h1>
        <Button asChild variant="outline">
          <Link href="/chat">チャットで質問 →</Link>
        </Button>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="allocation">配分</TabsTrigger>
          <TabsTrigger value="backtest">バックテスト</TabsTrigger>
          <TabsTrigger value="explain">AI説明</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <MetricsTable
              metrics={portfolio.metrics}
              strategy={portfolio.strategy}
            />
            <AllocationChart allocations={portfolio.allocations} size="lg" />
          </div>
        </TabsContent>

        <TabsContent value="allocation" className="mt-6">
          <AllocationTable
            allocations={portfolio.allocations}
            currency={portfolio.currency}
          />
        </TabsContent>

        <TabsContent value="backtest" className="mt-6">
          {backtestLoading ? (
            <div className="flex h-64 items-center justify-center">
              <p className="text-muted-foreground">バックテスト実行中...</p>
            </div>
          ) : backtest ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>パフォーマンスチャート（{backtest.period.years}年間）</CardTitle>
                </CardHeader>
                <CardContent>
                  <BacktestChart
                    timeSeries={backtest.time_series}
                    benchmarks={backtest.benchmark_comparison}
                  />
                </CardContent>
              </Card>

              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">累積リターン</p>
                    <p className="text-xl font-bold">
                      {(backtest.metrics.total_return * 100).toFixed(1)}%
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">CAGR</p>
                    <p className="text-xl font-bold">
                      {(backtest.metrics.cagr * 100).toFixed(2)}%
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">最大DD</p>
                    <p className="text-xl font-bold text-destructive">
                      {(backtest.metrics.max_drawdown * 100).toFixed(1)}%
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">シャープレシオ</p>
                    <p className="text-xl font-bold">
                      {backtest.metrics.sharpe_ratio.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {backtest.annual_returns.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>年次リターン</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <PerformanceChart annualReturns={backtest.annual_returns} />
                  </CardContent>
                </Card>
              )}

              <p className="text-xs text-muted-foreground">{backtest.disclaimer}</p>
            </div>
          ) : (
            <p className="text-center text-muted-foreground">
              バックテストデータがありません。
            </p>
          )}
        </TabsContent>

        <TabsContent value="explain" className="mt-6">
          {explanation ? (
            <Card>
              <CardContent className="prose prose-sm max-w-none pt-6">
                <div
                  dangerouslySetInnerHTML={{
                    __html: explanation
                      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                      .replace(/\n/g, "<br />"),
                  }}
                />
              </CardContent>
            </Card>
          ) : (
            <div className="flex flex-col items-center gap-4 py-12">
              <p className="text-muted-foreground">
                AIにポートフォリオの説明を生成させましょう。
              </p>
              <Button onClick={handleExplain} disabled={explainLoading}>
                {explainLoading ? "生成中..." : "AI説明を生成する"}
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
