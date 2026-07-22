import glob
import os

from app.core.config import settings
from app.retrieval.vector_store import store
from app.services.embedding_service import embed


async def build_index() -> int:
    paths = sorted(glob.glob(os.path.join(settings.docs_dir, "*.md")))
    texts = [open(p, encoding="utf-8").read().strip() for p in paths]
    if not texts:
        return 0
    vectors = await embed(texts)
    store.index(texts, vectors)
    return len(texts)
