import time
from collections.abc import AsyncIterator

from app.core.config import settings
from app.retrieval.vector_store import store
from app.schemas.chat import Metrics
from app.services.embedding_service import embed
from app.services.llm_service import stream_completion

SYSTEM = "Answer the question using only the provided context. If the context is insufficient, say so."


async def run(history: list[dict], query: str) -> AsyncIterator:
    metrics = Metrics()
    start = time.perf_counter()

    query_vector = (await embed(query))[0]
    matches = store.search(query_vector, settings.retrieval_top_k)
    context = "\n\n".join(text for text, _ in matches)

    messages = [{"role": "system", "content": SYSTEM}] + history + [
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]
    metrics.llm_calls = 1

    first = True
    stream = await stream_completion(messages)
    async for chunk in stream:
        if chunk.usage:
            metrics.prompt_tokens = chunk.usage.prompt_tokens
            metrics.completion_tokens = chunk.usage.completion_tokens
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            if first:
                metrics.ttft_ms = (time.perf_counter() - start) * 1000
                first = False
            yield delta

    metrics.total_ms = (time.perf_counter() - start) * 1000
    yield metrics
