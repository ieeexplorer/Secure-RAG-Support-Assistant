from __future__ import annotations

from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import Settings
from app.rag.types import ChunkRecord


class ChromaVectorStore:
    def __init__(self, settings: Settings) -> None:
        self._client = PersistentClient(path=str(settings.vector_store_path))
        self._embedding_function = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
        self._collection_name = settings.collection_name
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> Collection:
        return self._client.get_or_create_collection(
            name=self._collection_name,
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        try:
            self._client.delete_collection(name=self._collection_name)
        except Exception:
            pass
        self._collection = self._get_or_create_collection()

    def upsert(self, chunks: list[ChunkRecord]) -> None:
        if not chunks:
            return

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                **chunk.metadata,
                "source": chunk.source,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
            }
            for chunk in chunks
        ]
        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, question: str, top_k: int) -> list[dict]:
        result = self._collection.query(query_texts=[question], n_results=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        rows: list[dict] = []
        for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
            score = 1.0 / (1.0 + float(distance))
            rows.append({"text": document, "metadata": metadata, "score": round(score, 4)})
        return rows
