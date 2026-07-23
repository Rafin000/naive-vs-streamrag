import asyncio
import json
import statistics

from app.retrieval.indexer import build_index
from app.schemas.chat import Metrics
from app.services import naive_rag_service, stream_rag_service
from benchmark.judge import score

PRICING = {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000}
PATHS = {"naive": naive_rag_service, "stream": stream_rag_service}


async def _run_one(service, question: str) -> tuple[str, Metrics]:
    answer, metrics = "", Metrics()
    async for piece in service.run([], question):
        if isinstance(piece, Metrics):
            metrics = piece
        elif isinstance(piece, str):
            answer += piece
    return answer, metrics


async def _run_path(name: str, cases: list[dict]) -> dict:
    ttfts, totals, costs, scores = [], [], [], []
    for case in cases:
        answer, m = await _run_one(PATHS[name], case["question"])
        ttfts.append(m.ttft_ms)
        totals.append(m.total_ms)
        costs.append(m.prompt_tokens * PRICING["prompt"] + m.completion_tokens * PRICING["completion"])
        scores.append(await score(case["question"], case["expected"], answer))
    return {
        "path": name,
        "avg_ttft_ms": round(statistics.mean(ttfts), 1),
        "avg_total_ms": round(statistics.mean(totals), 1),
        "avg_cost_usd": round(statistics.mean(costs), 8),
        "avg_score": round(statistics.mean(scores), 2),
    }


async def main() -> None:
    await build_index()
    cases = json.load(open("app/data/testset.json", encoding="utf-8"))
    results = [await _run_path(name, cases) for name in PATHS]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
