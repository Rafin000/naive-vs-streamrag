import asyncio
import time
from collections.abc import AsyncIterator

from app.core.config import settings
from app.retrieval.vector_store import store
from app.schemas.chat import Metrics, Thinking
from app.services.embedding_service import embed
from app.services.llm_service import stream_completion

FRAMING_SYSTEM = (
    "Reply with only a one or two word acknowledgement that you are looking it up, such as "
    "'Checking…' or 'One sec…'. Do not state any facts, numbers, or names."
)
GROUNDED_SYSTEM = "Answer the question using only the provided context. If the context is insufficient, say so."


async def _retrieve(query: str) -> str:
    query_vector = (await embed(query))[0]
    matches = store.search(query_vector, settings.retrieval_top_k)
    return "\n\n".join(text for text, _ in matches)


def _accumulate_usage(chunk, metrics: Metrics) -> None:
    if chunk.usage:
        metrics.prompt_tokens += chunk.usage.prompt_tokens
        metrics.completion_tokens += chunk.usage.completion_tokens


async def run(history: list[dict], query: str) -> AsyncIterator:
    metrics = Metrics()
    start = time.perf_counter()

    retrieval = asyncio.create_task(_retrieve(query))

    # Phase 1: a short, fact-free framing line that overlaps retrieval and gives the user a
    # first token quickly. Capped short so it costs little and finishes about when retrieval does.
    metrics.llm_calls += 1
    framing = [{"role": "system", "content": FRAMING_SYSTEM}, {"role": "user", "content": query}]
    stream = await stream_completion(framing, max_tokens=6)
    first = True
    async for chunk in stream:
        _accumulate_usage(chunk, metrics)
        if chunk.choices and chunk.choices[0].delta.content:
            if first:
                metrics.ttft_ms = (time.perf_counter() - start) * 1000
                first = False
            yield Thinking(text=chunk.choices[0].delta.content)

    context = await retrieval

    # Phase 2: the grounded answer, streamed into the answer area.
    metrics.llm_calls += 1
    grounded = [{"role": "system", "content": GROUNDED_SYSTEM}] + history + [
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]
    stream = await stream_completion(grounded)
    async for chunk in stream:
        _accumulate_usage(chunk, metrics)
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

    metrics.total_ms = (time.perf_counter() - start) * 1000
    yield metrics
