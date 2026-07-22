# Reranking
Reranking is a second pass that reorders retrieved candidates by relevance. A fast vector search
first pulls a broad set of candidates, then a more precise but slower model rescores them so the
best passages rise to the top. Reranking improves answer quality when the initial similarity
search is noisy, at the cost of extra latency and compute.
