import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
      {/* Hero */}
      <section className="flex flex-col items-center gap-6 py-12 text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          AI ポートフォリオアドバイザー
        </h1>
        <p className="max-w-xl text-lg text-muted-foreground">
          あなたのリスク許容度に合わせた最適なポートフォリオをAIが提案します。
          日米の金融資産データに基づく教育目的の情報提供サービスです。
        </p>
        <Button asChild size="lg" className="mt-4">
          <Link href="/risk-assessment">リスク診断を始める →</Link>
        </Button>
        <p className="text-sm text-muted-foreground">
          ※ ログイン不要。診断結果はブラウザ内に一時保存されます。
        </p>
      </section>

      {/* Features */}
      <section className="grid gap-6 py-8 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="mb-3 text-3xl">📋</div>
            <h3 className="mb-2 font-semibold">リスク診断</h3>
            <p className="text-sm text-muted-foreground">
              8つの質問に答えるだけで、あなたのリスク許容度を1〜10のスコアで数値化します。
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="mb-3 text-3xl">📊</div>
            <h3 className="mb-2 font-semibold">ポートフォリオ最適化</h3>
            <p className="text-sm text-muted-foreground">
              最新の金融工学手法（HRP、最小分散、最大シャープレシオ等）で最適な配分を計算します。
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="mb-3 text-3xl">💬</div>
            <h3 className="mb-2 font-semibold">AIチャット</h3>
            <p className="text-sm text-muted-foreground">
              AIアドバイザーにポートフォリオについて何でも質問できます。初心者にもわかりやすく解説します。
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
