# Naive RAG vs StreamRAG

A small retrieval-augmented agent that answers questions over a document set **two different
ways** and measures the trade-off between them.

- **Naive RAG** runs sequentially: embed the query → retrieve top-k documents → generate the
  answer. One model call, lowest cost, but the user sees nothing until retrieval finishes, so
  time to first token (TTFT) is high.
- **StreamRAG** runs in two phases. It launches retrieval as a concurrent task and *immediately*
  streams a short provisional answer from the model's own knowledge, then continues straight into
  a grounded answer once the retrieved context arrives. First token appears much sooner, at the
  cost of a second model call.

Both paths use the same model, embeddings, documents, and top-k, so the comparison is fair. It
exposes the real trade-off:

> **StreamRAG trades higher total cost for a much lower time to first token.**
> **Naive RAG is cheaper and slightly more accurate, but slower to respond.**

The frontend shows live metrics under each answer (TTFT, total time, tokens, cost). The benchmark
script runs the full head-to-head over a test set and scores accuracy with an LLM judge.

## How it works

### The two RAG paths

**Naive** (`app/services/naive_rag_service.py`) — one prompt, one call:

```
embed(query) → vector search → build prompt with context → stream one grounded answer
```

The prompt can't be sent until retrieval is done, because the context is part of the prompt.
That single dependency is why TTFT is high.

**StreamRAG** (`app/services/stream_rag_service.py`) — two prompts, two calls, overlapped:

```
start retrieval as a background task
   └─ meanwhile: stream a quick provisional answer (no context)   ← first token appears here
when retrieval finishes:
   └─ stream the grounded answer, continuing from the provisional draft
```

The provisional phase needs no context, so it can start instantly while retrieval runs in
parallel via `asyncio`. The grounded phase receives the provisional draft as a prior assistant
turn, so the two read as one continuous answer instead of two separate replies.

### The agent harness

Around the model, the agent (`app/services/agent_service.py`) adds three things the assessment
asks for:

- **Tool / function calling** — a calculator (`app/tools/calculator.py`). Arithmetic queries are
  computed exactly with a safe AST evaluator instead of being guessed by the model.
- **Memory** — a per-session message list (`app/memory/session_store.py`) resent each turn so the
  agent remembers the conversation.
- **Context compression** — when a session's history passes a token budget, the oldest turns are
  summarized by a **sub-agent** (`app/agents/summarizer.py`) and replaced with a short summary,
  keeping recent turns verbatim.

### Retrieval

Documents in `app/data/docs/` are embedded once at startup and stored in an in-memory NumPy
cosine store (`app/retrieval/vector_store.py`). This is intentional for the assessment; the
store's interface is tiny, so it can be swapped for pgvector / Qdrant / Vectorize in production.

## Project layout

```
app/
  core/         config (secrets via pydantic-settings) and logging
  api/routes/   chat (SSE streaming) and health endpoints
  schemas/      request and metrics models
  services/     embedding, llm, naive_rag, stream_rag, agent orchestration
  agents/       summarizer sub-agent (also used for memory compression)
  tools/        calculator tool
  memory/       in-memory per-session message store
  retrieval/    in-memory cosine vector store and startup indexer
  data/         knowledge docs and test set
benchmark/      benchmark runner and llm-as-judge scorer
frontend/       single-page client with a live metrics panel
```

## Setup

Requires **Python 3.9+** and an OpenAI API key.

```bash
# 1. clone and enter the project
cd naive-vs-streamrag

# 2. create a virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. add your OpenAI key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...
```

`.env` is git-ignored, so your key is never committed.

## Run the server

```bash
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000`. On startup it embeds the documents in
`app/data/docs/` and logs how many were indexed.

Check it is up:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## Use the frontend

Open `frontend/index.html` in your browser. Type a question, pick **Naive** or **Stream**, and
press Ask. The answer streams in live, and the metrics panel below it shows TTFT, total time,
tokens, and cost. Switch the dropdown and ask the same question to feel the TTFT difference.

The frontend expects the server on `http://localhost:8000` (CORS is open in dev).

## API

`POST /ask` — streams the answer as Server-Sent Events.

Request body:

```json
{ "session_id": "abc", "query": "How does StreamRAG reduce latency?", "path": "stream" }
```

`path` is `"naive"` or `"stream"`. The response is an SSE stream of `data: {"token": "..."}`
events, followed by a `metrics` event with the timing and token counts, then a `done` event.

Example with curl:

```bash
curl -N -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","query":"What is time to first token?","path":"stream"}'
```

## Benchmark

Runs every question in `app/data/testset.json` through both paths and reports averaged metrics,
scoring accuracy with an LLM judge (`benchmark/judge.py`).

```bash
python -m benchmark.benchmark
```

Reports, per path: average TTFT, average total latency, average cost in USD, and average
accuracy score (0–5).

## Docker

```bash
docker compose up --build
```

Reads `OPENAI_API_KEY` from your `.env` and serves the API on port 8000.

## Configuration

Set in `.env` (see `.env.example`); all but the key have defaults:

| Variable | Default | Meaning |
|---|---|---|
| `OPENAI_API_KEY` | — (required) | OpenAI API key |
| `CHAT_MODEL` | `gpt-4o-mini` | generation model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | embedding model |
| `RETRIEVAL_TOP_K` | `3` | documents retrieved per query |
| `CONTEXT_TOKEN_BUDGET` | `2000` | history size before compression kicks in |

## Design notes

- **Same model both paths** so the benchmark measures the *strategy*, not a model difference.
- **In-memory store and memory** are deliberate for a self-contained assessment; production would
  use a vector database and an async ingestion pipeline (an endpoint queues documents; a worker
  chunks, embeds, and upserts them), plus a shared session store such as Redis.
- **Honest trade-off:** StreamRAG's provisional phase answers from the model's own knowledge
  before grounding, so it can occasionally state something the grounded phase then corrects. That
  is the accuracy cost of lower latency, and the benchmark reflects it.
