# Async Concurrency
Async concurrency lets a program start slow input/output work and do other work while waiting,
instead of blocking. In Python, asyncio runs coroutines on a single thread and can await many
network calls at once. StreamRAG uses this to overlap retrieval with the request so the system
spends less wall-clock time idle, which lowers time to first token.
