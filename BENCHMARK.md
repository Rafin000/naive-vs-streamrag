# Benchmark: Naive RAG vs StreamRAG

Both paths were run over the same fixed test set, using the same model
(`gpt-4o-mini`), embeddings (`text-embedding-3-small`), documents, and `top_k = 3`, so any
difference is due to the **strategy**, not the setup.

## Test set

15 questions about the fictional **Azure Bay Resort**, each with an expected answer defined up
front (`app/data/testset.json`). They are realistic guest questions: room categories and prices,
whether there is a restaurant, the Saltwater Grill menu, check-in/out times, airport pickup cost,
spa prices, water sports, breakfast hours, cancellation policy, pets, kids, wifi/parking, and how
to book. The facts are invented, so a correct answer can only come from retrieval — that makes
the accuracy score a real test of grounding.

## How to reproduce

```bash
python -m benchmark.benchmark
```

For each question it runs both paths, records timing and token usage, and scores the answer 0–5
with an LLM judge (`benchmark/judge.py`) against the expected answer. It prints the per-path
averages.

## Results

Averages over the 15 questions (one run; numbers vary a little run to run):

| Metric | Naive RAG | StreamRAG | Winner |
|---|---|---|---|
| Time to first token | 1178 ms | **635 ms** | StreamRAG (~46% faster) |
| Total response time | **1674 ms** | 1762 ms | Naive (~5% faster) |
| Cost per query | **$0.000064** | $0.000075 | Naive (~17% cheaper) |
| LLM calls per query | **1** | 2 | Naive |
| Accuracy (0–5, LLM judge) | 4.87 | 4.93 | tie |

## Reading the numbers

- **Speed (TTFT):** StreamRAG nearly **halves** time to first token, because it streams a short
  "thinking" line while retrieval runs in parallel, instead of waiting for retrieval like Naive.
  This is the metric StreamRAG is designed to win, and it does.
- **Speed (total):** Naive is slightly faster end-to-end. StreamRAG makes **two** model calls
  (framing + grounded) in sequence, so its total time is a bit higher. Note StreamRAG's *first
  answer* token also lands later than Naive's — it wins "first sign of life," not "first answer."
- **Cost:** Naive is cheaper — one call vs two, and fewer tokens.
- **Accuracy:** effectively tied and high for both (4.87 vs 4.93, within run-to-run noise). The
  hotel facts are only knowable from the documents, so both paths are genuinely grounded.
- **Failures:** no failed requests across the run.

## Why StreamRAG doesn't win total time here

Retrieval in this project is a fast in-memory NumPy cosine lookup (a few milliseconds plus one
embedding call). When retrieval is that fast, there is almost nothing to hide behind the thinking
line, so the extra framing call is mostly overhead on total time and cost. StreamRAG's advantage
grows as **retrieval latency grows** — a remote vector database, a web-search tool, or a
spoken/streaming interface where retrieval starts before the user has finished speaking. In those
settings the thinking line covers real waiting time and StreamRAG pulls ahead on perceived speed.

## Conclusion — when to use which

- **Use Naive RAG** when retrieval is fast and local, and cost or total latency matter. It is
  cheaper, simpler, and slightly faster end-to-end, with equal accuracy.
- **Use StreamRAG** when retrieval is slow (remote store, web search) or when perceived
  responsiveness matters (voice or chat UIs), and the extra call is an acceptable price for a
  much faster first token.

The honest summary: **StreamRAG buys a big drop in time-to-first-token with a small increase in
total time and cost, at equal accuracy.** Whether that trade is worth it depends entirely on how
slow your retrieval is and how much perceived latency matters to your users.
