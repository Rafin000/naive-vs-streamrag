from collections.abc import AsyncIterator

from app.core.config import settings
from app.services.openai_client import client


async def stream_completion(messages: list[dict]) -> AsyncIterator:
    return await client.chat.completions.create(
        model=settings.chat_model,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )


async def complete(messages: list[dict]) -> str:
    resp = await client.chat.completions.create(
        model=settings.chat_model, messages=messages
    )
    return resp.choices[0].message.content or ""
