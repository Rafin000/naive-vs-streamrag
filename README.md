# StreamRAG Agent

A small agent that answers questions over a document set two ways and compares them:

- **Naive RAG** runs sequentially: embed the query, retrieve top-k, then generate.
- **StreamRAG** overlaps retrieval with the request and streams tokens to cut time to first token.

Both paths share the same model, embeddings, and prompt so the comparison is fair. The frontend
shows live metrics per answer (TTFT, total time, tokens, cost) and a benchmark script runs the
full head-to-head over a test set.

## Architecture

```
app/
  core/         config (secrets via pydantic-settings) and logging
  api/routes/   chat and health endpoints
  schemas/      request and metrics models
  services/     embedding, llm, naive_rag, stream_rag, agent orchestration
  agents/       summarizer sub-agent (also used for memory compression)
  tools/        calculator tool
  memory/       in-memory per-session message store
  retrieval/    in-memory cosine vector store and startup indexer
  data/         knowledge docs and test set
benchmark/      benchmark runner and llm-as-judge scorer
frontend/       single-page client with a metrics panel
```

The agent adds three things around the model: a **tool** (calculator), **memory** (the message
list resent each turn), and **compression** (older turns are summarized once they pass a token
budget). Documents are embedded once at startup; production would replace this with an async
ingestion queue writing to a real vector database.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
uvicorn app.main:app --reload
```

Open `frontend/index.html` in a browser and ask a question. Toggle Naive vs Stream to compare.

## Benchmark

```bash
python -m benchmark.benchmark
```

Reports average TTFT, total latency, cost, and an LLM-judged accuracy score for each path.

## Docker

```bash
docker compose up --build
```

## Notes

- Model: `gpt-4o-mini` for generation, `text-embedding-3-small` for embeddings.
- Secrets are read from environment / `.env` and never committed.
- The vector store and session memory are in-memory by design for this assessment; the
  interfaces are small so they can be swapped for pgvector/Qdrant and Redis in production.
