from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.eval.metrics import faithfulness_score, relevance_score, retrieval_hit_score
from app.rag.chunking import chunk_document
from app.rag.generation import AnswerGenerator, select_relevant_chunks
from app.rag.loaders import load_documents
from app.rag.vector_store import ChromaVectorStore
from app.schemas import AnswerResponse, Citation, EvaluationSummary, IngestResponse


class RAGAssistant:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._store = ChromaVectorStore(settings)
        self._generator = AnswerGenerator(settings)

    def ingest(self, source_dir: Path | None = None, rebuild: bool = False) -> IngestResponse:
        kb_dir = source_dir or self._settings.knowledge_base_dir
        documents = load_documents(kb_dir)

        if rebuild:
            self._store.reset()

        all_chunks = []
        for document in documents:
            all_chunks.extend(chunk_document(document))

        self._store.upsert(all_chunks)
        return IngestResponse(
            source_dir=str(kb_dir),
            indexed_documents=len(documents),
            indexed_chunks=len(all_chunks),
        )

    def answer(self, question: str, top_k: int | None = None) -> AnswerResponse:
        effective_top_k = top_k or self._settings.top_k
        retrieved = self._store.query(question=question, top_k=effective_top_k)
        selected_chunks = select_relevant_chunks(question, retrieved, max_chunks=3)
        answer_text, fallback_used = self._generator.generate(question, selected_chunks)

        citations = [
            Citation(
                source=item["metadata"].get("source", "unknown"),
                line_start=item["metadata"].get("line_start"),
                line_end=item["metadata"].get("line_end"),
                snippet=item["text"][:240],
            )
            for item in selected_chunks
        ]

        confidence = round(sum(item["score"] for item in retrieved) / len(retrieved), 4) if retrieved else 0.0
        if confidence < self._settings.min_confidence:
            fallback_used = True
            answer_text = (
                f"Evidence is weak for this question. {answer_text} "
                "Treat this as a retrieval hint and verify against the cited sources."
            )

        evaluation = EvaluationSummary(
            relevance=relevance_score(question, answer_text),
            faithfulness=faithfulness_score(answer_text, retrieved),
            retrieval_hit=retrieval_hit_score(None, [item.model_dump() for item in citations]),
        )

        return AnswerResponse(
            answer=answer_text,
            citations=citations,
            confidence=confidence,
            evaluation=evaluation,
            fallback_used=fallback_used,
            retrieved_context=retrieved,
        )
