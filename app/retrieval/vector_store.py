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
        matrix = self._vectors.astype(np.float64)
        q = np.asarray(query_vector, dtype=np.float64)
        dots = (matrix * q).sum(axis=1)
        denom = np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)
        sims = np.zeros(len(matrix))
        np.divide(dots, denom, out=sims, where=denom > 0)
        top = np.argsort(-sims)[:k]
        return [(self._texts[i], float(sims[i])) for i in top]


store = VectorStore()
