import json
import time
from collections.abc import AsyncIterator

from app.agents.summarizer import summarize
from app.core.config import settings
from app.memory.session_store import memory
from app.schemas.chat import Metrics, ToolCall
from app.services import naive_rag_service, stream_rag_service
from app.services.openai_client import client
from app.tools.calculator import CALCULATOR_TOOL, evaluate, looks_like_math

_PATHS = {"naive": naive_rag_service, "stream": stream_rag_service}

TOOL_SYSTEM = "You are a helpful assistant. Use the calculator tool for any arithmetic instead of computing it yourself."


def _estimate_tokens(history: list[dict]) -> int:
    return sum(len(m["content"]) for m in history if m.get("content")) // 4


async def _compress(session_id: str, history: list[dict]) -> list[dict]:
    if _estimate_tokens(history) <= settings.context_token_budget:
        return history
    old, recent = history[:-4], history[-4:]
    summary = await summarize(old)
    compressed = [{"role": "system", "content": f"Summary so far: {summary}"}] + recent
    memory.replace(session_id, compressed)
    return compressed


async def _tool_agent(history: list[dict], query: str) -> AsyncIterator:
    metrics = Metrics()
    start = time.perf_counter()
    messages = [{"role": "system", "content": TOOL_SYSTEM}] + history + [{"role": "user", "content": query}]

    decision = await client.chat.completions.create(
        model=settings.chat_model, messages=messages, tools=[CALCULATOR_TOOL]
    )
    metrics.llm_calls += 1
    if decision.usage:
        metrics.prompt_tokens += decision.usage.prompt_tokens
        metrics.completion_tokens += decision.usage.completion_tokens

    choice = decision.choices[0].message
    if not choice.tool_calls:
        yield choice.content or ""
        metrics.ttft_ms = metrics.total_ms = (time.perf_counter() - start) * 1000
        yield metrics
        return

    call = choice.tool_calls[0]
    args = json.loads(call.function.arguments or "{}")
    result = evaluate(args.get("expression", ""))
    yield ToolCall(tool=call.function.name, result=str(result))

    messages.append({
        "role": "assistant",
        "content": choice.content,
        "tool_calls": [
            {"id": call.id, "type": "function",
             "function": {"name": call.function.name, "arguments": call.function.arguments}}
        ],
    })
    messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})

    metrics.llm_calls += 1
    first = True
    stream = await client.chat.completions.create(
        model=settings.chat_model, messages=messages, stream=True, stream_options={"include_usage": True}
    )
    async for chunk in stream:
        if chunk.usage:
            metrics.prompt_tokens += chunk.usage.prompt_tokens
            metrics.completion_tokens += chunk.usage.completion_tokens
        if chunk.choices and chunk.choices[0].delta.content:
            if first:
                metrics.ttft_ms = (time.perf_counter() - start) * 1000
                first = False
            yield chunk.choices[0].delta.content

    metrics.total_ms = (time.perf_counter() - start) * 1000
    yield metrics


async def handle(session_id: str, query: str, path: str) -> AsyncIterator:
    memory.append(session_id, {"role": "user", "content": query})
    history = await _compress(session_id, memory.get(session_id))

    runner = _tool_agent(history[:-1], query) if looks_like_math(query) else _PATHS.get(path, naive_rag_service).run(history[:-1], query)

    answer = ""
    async for piece in runner:
        if isinstance(piece, str):
            answer += piece
        yield piece
    memory.append(session_id, {"role": "assistant", "content": answer})
