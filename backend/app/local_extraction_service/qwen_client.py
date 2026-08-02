import asyncio
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key="EMPTY", base_url=settings.vllm_base_url)

# Caps how many Qwen requests are in flight at once, across every PDF being
# processed concurrently. vLLM does its own continuous batching on top of
# this -- this is purely a "don't flood the server" ceiling.
_semaphore = asyncio.Semaphore(settings.qwen_max_concurrency)


async def call_structured(
    messages: list[dict], schema: type[BaseModel], max_tokens: int
) -> BaseModel:
    """Sends one chat-completion request to the vLLM-hosted Qwen model,
    constrained to `schema` via guided decoding, and returns the parsed
    result.

    Raises on any failure (timeout, connection error, malformed output) --
    callers decide whether that should fail the whole PDF or just one batch.
    """
    async with _semaphore:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=settings.vllm_model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.2,
                # vLLM's legacy `extra_body={"guided_json": ...}` path silently
                # ignores the schema for multimodal (image-containing)
                # requests on this server -- confirmed by testing with a
                # bogus/omitted guided_decoding_backend and getting identical,
                # unconstrained output either way. The standard OpenAI
                # `response_format` structured-output API is enforced
                # correctly even with images, so that's used instead.
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema.model_json_schema(),
                        "strict": True,
                    },
                },
            ),
            timeout=settings.vllm_request_timeout_seconds,
        )

    raw_content = response.choices[0].message.content
    try:
        return schema.model_validate_json(raw_content)
    except Exception:
        logger.error(
            "Structured output failed schema validation: schema=%s raw_response=%r",
            schema.__name__, raw_content,
        )
        raise
