"""Chat SSE endpoint — streams Claude responses via Server-Sent Events."""

import json
import logging

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.schemas.chat import ChatRequest
from src.app.services.ai_advisor import SYSTEM_PROMPT, AIAdvisor
from src.app.services.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

AI_MODEL = "claude-sonnet-4-5-20250514"


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Streaming chat endpoint using Claude API with SSE.

    Flow:
    1. Check usage budget (429 if exceeded)
    2. Build system prompt + portfolio context
    3. Stream Claude response via SSE
    4. Record usage after completion
    """
    tracker = UsageTracker(db)
    await tracker.check_budget()

    # Build system prompt with portfolio context
    advisor = AIAdvisor()
    context = advisor.build_chat_context(
        request.portfolio_context.model_dump() if request.portfolio_context else None,
    )
    system_prompt = SYSTEM_PROMPT
    if context:
        system_prompt += f"\n\nユーザーの現在のポートフォリオ情報:\n{context}"

    # Convert messages to anthropic format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def event_stream():
        input_tokens = 0
        output_tokens = 0
        try:
            async with client.messages.stream(
                model=AI_MODEL,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            data = json.dumps(
                                {"type": "text-delta", "text": event.delta.text},
                                ensure_ascii=False,
                            )
                            yield f"data: {data}\n\n"

                # Get final message for usage
                final = await stream.get_final_message()
                input_tokens = final.usage.input_tokens
                output_tokens = final.usage.output_tokens

            # Send finish event
            finish_data = json.dumps(
                {
                    "type": "finish",
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                },
                ensure_ascii=False,
            )
            yield f"data: {finish_data}\n\n"

            # Record usage (need fresh session since streaming is outside request lifecycle)
            await tracker.record_usage(
                endpoint="chat",
                model=AI_MODEL,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            await db.commit()

        except anthropic.APIError as e:
            logger.exception("Claude API error during chat stream")
            error_data = json.dumps(
                {"type": "error", "message": str(e)},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"
        except Exception as e:
            logger.exception("Unexpected error during chat stream")
            error_data = json.dumps(
                {"type": "error", "message": "チャット応答中にエラーが発生しました。"},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
