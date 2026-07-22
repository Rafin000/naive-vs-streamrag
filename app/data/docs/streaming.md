# Streaming and Time to First Token
Time to first token (TTFT) is the delay before a user sees the first piece of a response.
Streaming responses lower perceived latency because tokens are shown as they are generated
instead of after the full completion. Server-Sent Events (SSE) are a common transport for
streaming token deltas from a backend to a browser.
