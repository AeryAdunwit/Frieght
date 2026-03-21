from __future__ import annotations

from ...sync_vectors import sync
from ...vector_search import load_topic_rows, search_knowledge


class KnowledgeService:
    def search(self, query: str, *, top_k: int = 5, threshold: float = 0.5):
        return search_knowledge(query, top_k=top_k, threshold=threshold)

    def load_topic_rows(self, topic: str, *, limit: int = 200):
        return load_topic_rows(topic, limit=limit)

    def sync_now(self):
        return sync()

