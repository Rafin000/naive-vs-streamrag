# Naive RAG vs StreamRAG

**▶ Live demo: http://16.171.174.104:8000** — hosted on AWS EC2; try it in your browser.

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
