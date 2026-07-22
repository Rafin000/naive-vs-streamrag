from app.core.config import settings
from app.services.openai_client import client


async def embed(texts: str | list[str]) -> list[list[float]]:
    if isinstance(texts, str):
        texts = [texts]
    resp = await client.embeddings.create(model=settings.embedding_model, input=texts)
    return [item.embedding for item in resp.data]
