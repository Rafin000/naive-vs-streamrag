# Vector Databases
A vector database stores embeddings and supports fast nearest-neighbor search over them.
Examples include pgvector, Qdrant, and Cloudflare Vectorize. They use approximate nearest
neighbor indexes so search stays fast as the number of vectors grows into the millions. This
project uses a simple in-memory NumPy store instead, which is fine for a small document set.
