from __future__ import annotations

from typing import Any, Callable

from .chunking import compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0
        # Chỉ dùng in-memory: nhánh ChromaDB không cần cho lab, và bật _use_chroma khi chưa có
        # client sẽ làm mọi method rẽ vào nhánh chưa cài đặt trên máy có sẵn chromadb.

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)  # copy để không sửa object của người gọi
        # doc_id trỏ về tài liệu gốc (bench.py đặt sẵn khi chunk "file#0"); mặc định là id của Document.
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
            "index": self._next_index,
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []
        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                # Mock/Local embedder đã chuẩn hoá nên dot == cosine; dùng cosine đầy đủ để an toàn
                # với backend trả vector chưa chuẩn hoá.
                "score": compute_similarity(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        self._store.extend(self._make_record(doc) for doc in docs)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # Lọc TRƯỚC rồi mới xếp hạng: nếu lấy top-k trước, các slot có thể bị chiếm hết bởi
        # chunk không khớp filter và kết quả rỗng dù store vẫn còn chunk hợp lệ.
        criteria = metadata_filter or {}
        candidates = [
            record for record in self._store
            if all(record["metadata"].get(key) == value for key, value in criteria.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        size_before = len(self._store)
        self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        return len(self._store) < size_before
