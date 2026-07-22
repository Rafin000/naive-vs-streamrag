from collections.abc import AsyncIterator

from app.agents.summarizer import summarize
from app.core.config import settings
from app.memory.session_store import memory
from app.services import naive_rag_service, stream_rag_service
from app.tools.calculator import maybe_calculate

_PATHS = {"naive": naive_rag_service, "stream": stream_rag_service}


def _estimate_tokens(history: list[dict]) -> int:
    return sum(len(m["content"]) for m in history) // 4


async def _compress(session_id: str, history: list[dict]) -> list[dict]:
    if _estimate_tokens(history) <= settings.context_token_budget:
        return history
    old, recent = history[:-4], history[-4:]
    summary = await summarize(old)
    compressed = [{"role": "system", "content": f"Summary so far: {summary}"}] + recent
    memory.replace(session_id, compressed)
    return compressed


async def handle(session_id: str, query: str, path: str) -> AsyncIterator:
    tool_result = maybe_calculate(query)
    memory.append(session_id, {"role": "user", "content": query})
    history = await _compress(session_id, memory.get(session_id))

    if tool_result is not None:
        answer = f"The result is {tool_result}."
        memory.append(session_id, {"role": "assistant", "content": answer})
        yield answer
        return

    service = _PATHS.get(path, naive_rag_service)
    answer = ""
    async for piece in service.run(history[:-1], query):
        if isinstance(piece, str):
            answer += piece
        yield piece
    memory.append(session_id, {"role": "assistant", "content": answer})
