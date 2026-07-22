import asyncio
import time
from collections.abc import AsyncIterator

from app.core.config import settings
from app.retrieval.vector_store import store
from app.schemas.chat import Metrics
from app.services.embedding_service import embed
from app.services.llm_service import stream_completion

DRAFT_SYSTEM = (
    "Give a brief initial answer to the question in one or two sentences from your own "
    "knowledge. Be concise and do not mention sources."
)
GROUNDED_SYSTEM = (
    "You already gave the user a brief initial reply. Using only the provided context, "
    "continue and refine that reply without repeating it, and do not add a preamble such as "
    "'based on the sources'. If the context is insufficient, say so."
)


async def _retrieve(query: str) -> str:
    query_vector = (await embed(query))[0]
    matches = store.search(query_vector, settings.retrieval_top_k)
    return "\n\n".join(text for text, _ in matches)


async def _stream(messages: list[dict], metrics: Metrics) -> AsyncIterator[str]:
    metrics.llm_calls += 1
    stream = await stream_completion(messages)
    async for chunk in stream:
        if chunk.usage:
            metrics.prompt_tokens += chunk.usage.prompt_tokens
            metrics.completion_tokens += chunk.usage.completion_tokens
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def run(history: list[dict], query: str) -> AsyncIterator:
    metrics = Metrics()
    start = time.perf_counter()

    retrieval = asyncio.create_task(_retrieve(query))

    draft = [{"role": "system", "content": DRAFT_SYSTEM}, {"role": "user", "content": query}]
    draft_text = ""
    first = True
    async for delta in _stream(draft, metrics):
        if first:
            metrics.ttft_ms = (time.perf_counter() - start) * 1000
            first = False
        draft_text += delta
        yield delta

    context = await retrieval
    yield "\n\n"
    grounded = [{"role": "system", "content": GROUNDED_SYSTEM}] + history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": draft_text},
        {"role": "user", "content": f"Context to refine your answer:\n{context}"},
    ]
    async for delta in _stream(grounded, metrics):
        yield delta

    metrics.total_ms = (time.perf_counter() - start) * 1000
    yield metrics
