# Naive RAG vs StreamRAG

A small full-stack agent that answers questions about a fictional hotel, **Azure Bay Resort**,
two different ways and measures the trade-off between them:

- **Naive RAG** runs sequentially: embed the query → retrieve top-k documents → generate one
  grounded answer. One model call, lowest cost, but nothing appears until retrieval finishes, so
  time to first token (TTFT) is high.
- **StreamRAG** launches retrieval as a concurrent task and *immediately* streams a short,
  fact-free "thinking" line (e.g. *"Checking…"*) while retrieval runs. When the documents arrive
  it streams the grounded answer. Two model calls, so the first token appears much sooner at the
  cost of slightly higher total time and cost.

Both paths use the same model, embeddings, documents, and top-k, so the comparison is fair.
See [BENCHMARK.md](BENCHMARK.md) for measured results; the short version:

> **StreamRAG nearly halves time-to-first-token; Naive is cheaper and slightly faster end-to-end.
> Accuracy is a tie. Use StreamRAG when retrieval is slow or perceived latency matters; use Naive
> when retrieval is fast and cost matters.**

The frontend is a chat UI that runs both paths on every message and tracks running averages.

## How it works

### The two RAG paths

**Naive** (`app/services/naive_rag_service.py`) — one prompt, one call:

```
embed(query) → vector search → build prompt with context → stream one grounded answer
```

The prompt can't be sent until retrieval is done (the context is part of the prompt). That single
dependency is why TTFT is high.

**StreamRAG** (`app/services/stream_rag_service.py`) — two calls, retrieval overlapped:

```
start retrieval as a concurrent asyncio task
   └─ meanwhile: stream a short fact-free "thinking" line   ← first token appears here
when retrieval finishes:
   └─ stream the grounded answer using the retrieved context
```

The thinking line needs no context, so it starts while retrieval runs in parallel (verified: the
retrieval task begins within ~4 ms and finishes before the framing model's first token). It is
deliberately **fact-free** — the documents hold private hotel details the model can't know, so a
provisional *answer* would hallucinate; a neutral acknowledgement can't.

### The agent harness

The agent (`app/services/agent_service.py`) wraps the model with:

- **Tool (real function calling)** — a calculator (`app/tools/calculator.py`). A cheap check
  routes arithmetic to a tool loop where the model is given the tool schema, **decides** to call
  `calculator(expression)`, the app evaluates it with a safe AST evaluator, and the model then
  **composes** the answer from the result. It is genuine OpenAI function calling, not a hardcoded
  reply.
- **Memory** — a per-session message list (`app/memory/session_store.py`) keyed by `session_id`
  and resent each turn, so follow-ups like *"how many guests does it fit?"* resolve from context.
- **Context compression** — when a session's history passes a token budget, the oldest turns are
  summarized by a **sub-agent** (`app/agents/summarizer.py`) and replaced with a short summary,
  keeping recent turns verbatim.

### Retrieval

The 19 documents in `app/data/docs/` are embedded once at startup and stored in an in-memory
NumPy cosine store (`app/retrieval/vector_store.py`). This is intentional for the assessment; the
interface is tiny, so it can be swapped for pgvector / Qdrant / Vectorize in production.

## Project layout

```
app/
  core/         config (secrets via pydantic-settings) and logging
  api/routes/   chat (SSE streaming) and health endpoints
  schemas/      request, metrics, thinking, and tool-call models
  services/     embedding, llm, naive_rag, stream_rag, agent orchestration
  agents/       summarizer sub-agent (also used for memory compression)
  tools/        calculator tool (function-calling schema + safe evaluator)
  memory/       in-memory per-session message store
  retrieval/    in-memory cosine vector store and startup indexer
  data/         hotel documents and the test set
benchmark/      benchmark runner and llm-as-judge scorer
frontend/       single-page chat UI with a running-averages panel
```

## Setup

Requires **Python 3.9+** and an OpenAI API key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set OPENAI_API_KEY=sk-... in .env
```

`.env` is git-ignored, so your key is never committed.

## Run

```bash
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`; on startup it embeds the hotel documents. Check it:

```bash
curl http://localhost:8000/health   # {"status":"ok"}
```

Then open `frontend/index.html` in a browser. Pick a question from the dropdown (or type your
own) and hit **Send** — each message runs **both** paths side by side, streaming live, and the
panel on the right tracks average TTFT, total time, tokens, and cost across the chat.

Things to try:
- A normal question (rooms, menu, spa, airport pickup) — watch StreamRAG's thinking line appear
  before Naive's answer.
- The calculator question (*"…Calculate 180 * 3"*) — the tool badge shows `tool called: calculator`.
- The Ocean View sequence in order — a follow-up like *"how many guests does it fit?"* resolves
  from memory.

## API

`POST /ask` streams Server-Sent Events. Body:

```json
{ "session_id": "abc", "query": "How much is an Ocean View room?", "path": "stream" }
```

`path` is `"naive"` or `"stream"`. Events: `data: {"token": …}` (answer tokens),
`event: thinking` (StreamRAG's framing line), `event: tool` (a tool call), `event: metrics`
(timings and token counts), then `event: done`.

## Benchmark

```bash
python -m benchmark.benchmark
```

Runs all 15 questions in `app/data/testset.json` through both paths and reports average TTFT,
total latency, cost, and an LLM-judged accuracy score. Results and discussion: [BENCHMARK.md](BENCHMARK.md).

## Docker

```bash
docker compose up --build
```

Reads `OPENAI_API_KEY` from `.env` and serves the API on port 8000.

## Configuration

Set in `.env` (see `.env.example`); all but the key have defaults:

| Variable | Default | Meaning |
|---|---|---|
| `OPENAI_API_KEY` | — (required) | OpenAI API key |
| `CHAT_MODEL` | `gpt-4o-mini` | generation model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | embedding model |
| `RETRIEVAL_TOP_K` | `3` | documents retrieved per query |
| `CONTEXT_TOKEN_BUDGET` | `2000` | history size before compression kicks in |

## Design notes and honest limitations

- **Same model both paths**, so the benchmark measures the *strategy*, not a model difference.
- **StreamRAG wins TTFT, not total time.** Because retrieval here is a fast in-memory lookup, the
  framing phase is pure overhead on total latency — StreamRAG's real advantage would grow if
  retrieval were slow (remote vector DB, web search, or streamed/voice input). See BENCHMARK.md.
- **In-memory store, memory, and sessions** are deliberate for a self-contained demo. Production
  would use a vector database with async ingestion, and a shared session store (e.g. Redis) keyed
  by the same `session_id` the frontend already sends. Reloading the page starts a new session.
