# StreamRAG
StreamRAG overlaps retrieval with the request lifecycle and streams the answer as it is
produced. Retrieval is launched as a concurrent task so the system spends less wall-clock
time blocked, and tokens are streamed to the client to minimize time to first token.
