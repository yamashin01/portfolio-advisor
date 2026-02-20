export default function RiskDisclosurePage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">リスク開示</h1>

      <div className="space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            投資に伴うリスクについて
          </h2>
          <p>
            金融商品への投資には、価格変動リスク、為替変動リスク、信用リスク、
            流動性リスク等の様々なリスクが伴います。
            投資元本を割り込む可能性があり、最悪の場合、投資した資金の全額を失う
            可能性があります。
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            本サービスの性質
          </h2>
          <ul className="list-disc space-y-2 pl-5">
            <li>
              本サービスは教育目的の情報提供であり、投資助言ではありません。
            </li>
            <li>
              ポートフォリオの配分提案は統計的手法に基づく参考情報であり、
              将来のパフォーマンスを保証するものではありません。
            </li>
            <li>
              バックテスト結果は過去のデータに基づく仮想的なシミュレーションであり、
              実際の取引コスト・税金・スリッページは考慮されていません。
            </li>
            <li>
              AI による説明は大規模言語モデルの出力であり、誤りを含む場合があります。
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            主なリスク要因
          </h2>
          <div className="space-y-3">
            <div>
              <h3 className="font-medium text-foreground">価格変動リスク</h3>
              <p>
                株式・ETF・REIT等の金融商品の価格は、市場の需給、経済指標、
                企業業績等の要因により変動します。
              </p>
            </div>
            <div>
              <h3 className="font-medium text-foreground">為替変動リスク</h3>
              <p>
                海外資産（米国ETF・債券等）は為替レートの変動により、
                円換算での価値が変動します。
              </p>
            </div>
            <div>
              <h3 className="font-medium text-foreground">金利変動リスク</h3>
              <p>
                債券の価格は市場金利の変動により影響を受けます。
                一般に金利が上昇すると債券価格は下落します。
              </p>
            </div>
            <div>
              <h3 className="font-medium text-foreground">流動性リスク</h3>
              <p>
                市場環境によっては、金融商品を希望する価格で売買できない場合があります。
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-2 text-base font-semibold text-foreground">
            ご利用にあたって
          </h2>
          <p>
            投資に関する最終決定は、ご自身の判断と責任において行ってください。
            必要に応じて、金融機関や税理士等の専門家にご相談ください。
          </p>
        </section>
      </div>
    </div>
  );
}
