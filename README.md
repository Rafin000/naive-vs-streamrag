# Naive RAG vs StreamRAG

A small full-stack agent that answers questions about a fictional hotel (**Azure Bay Resort**)
two ways and compares them:

- **Naive RAG** — embed → retrieve → answer. One model call; nothing appears until retrieval
  finishes, so time to first token (TTFT) is high.
- **StreamRAG** — starts retrieval in parallel and streams a short "thinking" line first, then the
  grounded answer once documents arrive. Two calls; much lower TTFT.

Same model, embeddings, documents, and `top_k` for both, so the comparison is fair. Measured
results are in [BENCHMARK.md](BENCHMARK.md): **StreamRAG nearly halves TTFT; Naive is cheaper and
slightly faster overall; accuracy ties.**

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set OPENAI_API_KEY=sk-...
uvicorn app.main:app --reload
```

Then open `frontend/index.html`. Pick a question (or type one) and hit **Send** — each message
runs both paths side by side with live metrics and running averages. (Or `docker compose up --build`.)

## Architecture

```
app/
  core/        config (secrets via pydantic-settings), logging
  api/routes/  chat (SSE streaming), health
  services/    embedding, llm, naive_rag, stream_rag, agent
  agents/      summarizer sub-agent (used for compression)
  tools/       calculator (function-calling tool)
  memory/      in-memory per-session store
  retrieval/   in-memory cosine vector store + startup indexer
  data/        hotel docs + test set
benchmark/     runner + llm-as-judge scorer
frontend/      chat UI
```

The agent adds a **tool** (real OpenAI function calling for arithmetic), **memory** (per session,
keyed by `session_id`), and **compression** (a sub-agent summarizes old turns past a token
budget). Documents are embedded once at startup into the in-memory store.

Benchmark: `python -m benchmark.benchmark`.

## Decisions and limitations

- Same model on both paths, so the benchmark measures the strategy, not the model.
- StreamRAG wins TTFT, not total time: retrieval here is a fast in-memory lookup, so the framing
  phase is mostly overhead. Its advantage grows when retrieval is slow (remote DB, web search,
  voice input).
- In-memory store, memory, and sessions are deliberate for a self-contained demo; production would
  use a vector database with async ingestion and a shared session store (e.g. Redis).
