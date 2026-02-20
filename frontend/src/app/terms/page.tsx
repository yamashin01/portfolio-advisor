export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">利用規約</h1>

      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            第1条（サービスの目的）
          </h2>
          <p>
            本サービス「AI ポートフォリオアドバイザー」（以下「本サービス」）は、
            金融資産の配分に関する教育目的の情報提供を行うものです。
            本サービスは投資助言業に該当するものではなく、
            特定の金融商品の売買を推奨するものではありません。
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            第2条（免責事項）
          </h2>
          <p>
            本サービスで提供される情報（ポートフォリオ配分、バックテスト結果、
            AI による説明等）は、過去のデータおよび統計的手法に基づく参考情報であり、
            将来の投資成果を保証するものではありません。
            投資判断はご自身の責任において行ってください。
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            第3条（データの正確性）
          </h2>
          <p>
            本サービスで使用する市場データは外部データプロバイダーから取得しており、
            その正確性・完全性・最新性を保証するものではありません。
            データの遅延・欠損・誤りが生じる場合があります。
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            第4条（AI 出力の性質）
          </h2>
          <p>
            本サービスの AI チャット機能は、大規模言語モデル（Claude）を使用しており、
            その出力は確率的に生成されるものです。AI の回答には誤りが含まれる場合があり、
            投資の根拠として使用することは推奨しません。
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            第5条（個人情報）
          </h2>
          <p>
            本サービスはユーザー登録・ログインを必要としません。
            リスク診断結果およびポートフォリオデータはブラウザ内にのみ一時保存され、
            サーバーには保存されません。
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            第6条（サービスの変更・中断）
          </h2>
          <p>
            運営者は、事前の通知なくサービスの内容変更、一時停止、
            または終了する場合があります。
          </p>
        </section>
      </div>
    </div>
  );
}
