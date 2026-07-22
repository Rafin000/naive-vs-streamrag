# Naive RAG
Naive RAG runs sequentially: embed the query, retrieve the top-k documents, build a prompt
with that context, then call the language model. It is simple and cheap (one model call) but
the user waits for retrieval to finish before generation can start, which increases TTFT.
