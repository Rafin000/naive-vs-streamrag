import numpy as np


class VectorStore:
    def __init__(self) -> None:
        self._texts: list[str] = []
        self._vectors: np.ndarray | None = None

    def index(self, texts: list[str], vectors: list[list[float]]) -> None:
        self._texts = texts
        self._vectors = np.array(vectors, dtype=np.float32)

    def search(self, query_vector: list[float], k: int) -> list[tuple[str, float]]:
        if self._vectors is None:
            return []
        q = np.array(query_vector, dtype=np.float32)
        norms = np.linalg.norm(self._vectors, axis=1) * np.linalg.norm(q) + 1e-9
        sims = (self._vectors @ q) / norms
        top = np.argsort(-sims)[:k]
        return [(self._texts[i], float(sims[i])) for i in top]


store = VectorStore()
