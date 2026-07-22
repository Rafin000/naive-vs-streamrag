from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    query: str
    path: str = "naive"  # naive | stream


class Metrics(BaseModel):
    total_ms: float = 0.0
    ttft_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    llm_calls: int = 0
