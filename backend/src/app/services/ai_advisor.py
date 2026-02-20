"""AI Advisor using Claude API for portfolio explanations and chat.

Handles:
- Portfolio explanation generation
- Chat context building
- System prompt management
"""

import logging

import anthropic

from src.app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
あなたは個人投資家向けの教育的なAIアドバイザーです。

ルール:
- 日本語で回答する
- 初心者にわかりやすい平易な表現を使う
- 具体的な売買タイミングの指示は絶対にしない
- リスクについて必ず言及する
- 「教育目的であり投資助言ではない」旨を適宜伝える
- ポートフォリオの配分理由を論理的に説明する
- 専門用語には簡単な説明を添える
"""

EXPLAIN_PROMPT_TEMPLATE = """\
以下のポートフォリオについて、個人投資家向けにわかりやすく説明してください。

**戦略**: {strategy}
**リスク許容度**: {risk_tolerance}

**配分**:
{allocations_text}

**指標**:
{metrics_text}

説明には以下を含めてください:
1. 配分の考え方（なぜこの配分なのか）
2. リスクについて（想定される下落幅など）
3. 重要な注意点（教育目的であり投資助言ではない旨）

Markdown形式で回答してください。
"""

# Default model for AI advisor
AI_MODEL = "claude-sonnet-4-5-20250514"


class AIAdvisor:
    """Claude API-based AI advisor for portfolio explanations."""

    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_explanation(
        self,
        strategy: str,
        risk_tolerance: str,
        allocations: list[dict],
        metrics: dict | None = None,
    ) -> tuple[str, dict]:
        """Generate a portfolio explanation.

        Returns
        -------
        tuple[str, dict]
            (explanation_text, usage_dict) where usage_dict has
            "input_tokens" and "output_tokens".
        """
        allocations_text = "\n".join(
            f"- {a.get('name_ja') or a['symbol']} ({a['symbol']}): {a['weight']:.0%}"
            for a in allocations
        )
        metrics_text = "なし"
        if metrics:
            parts = []
            if metrics.get("expected_return") is not None:
                parts.append(f"期待リターン: {metrics['expected_return']:.2%}")
            if metrics.get("volatility") is not None:
                parts.append(f"ボラティリティ: {metrics['volatility']:.2%}")
            if metrics.get("sharpe_ratio") is not None:
                parts.append(f"シャープレシオ: {metrics['sharpe_ratio']:.2f}")
            metrics_text = " / ".join(parts) if parts else "なし"

        user_message = EXPLAIN_PROMPT_TEMPLATE.format(
            strategy=strategy,
            risk_tolerance=risk_tolerance,
            allocations_text=allocations_text,
            metrics_text=metrics_text,
        )

        response = await self.client.messages.create(
            model=AI_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        explanation = response.content[0].text
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return explanation, usage

    def build_chat_context(
        self,
        portfolio_context: dict | None = None,
    ) -> str:
        """Build context string for chat from portfolio data."""
        if not portfolio_context:
            return ""

        parts = []
        if portfolio_context.get("strategy"):
            parts.append(f"戦略: {portfolio_context['strategy']}")
        if portfolio_context.get("risk_tolerance"):
            parts.append(f"リスク許容度: {portfolio_context['risk_tolerance']}")

        allocs = portfolio_context.get("allocations", [])
        if allocs:
            parts.append("ポートフォリオ配分:")
            for a in allocs:
                name = a.get("name_ja") or a.get("symbol", "")
                parts.append(f"  - {name}: {a.get('weight', 0):.0%}")

        metrics = portfolio_context.get("metrics")
        if metrics:
            parts.append("指標:")
            if metrics.get("expected_return") is not None:
                parts.append(f"  - 期待リターン: {metrics['expected_return']:.2%}")
            if metrics.get("volatility") is not None:
                parts.append(f"  - ボラティリティ: {metrics['volatility']:.2%}")
            if metrics.get("sharpe_ratio") is not None:
                parts.append(f"  - シャープレシオ: {metrics['sharpe_ratio']:.2f}")

        return "\n".join(parts)
