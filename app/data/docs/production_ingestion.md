# Production Ingestion
In production, new knowledge is added through an ingestion pipeline rather than at startup. An
endpoint receives documents and places them on a queue, and a worker chunks, embeds, and upserts
them into a vector database asynchronously. This keeps the request fast, handles large batches,
and lets the knowledge base grow without redeploying the application.
