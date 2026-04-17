from __future__ import annotations

import hashlib

from app.rag.types import ChunkRecord, SourceDocument


def chunk_document(document: SourceDocument, chunk_size: int = 4, overlap: int = 1) -> list[ChunkRecord]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    indexed_lines = [(index, line) for index, line in enumerate(document.lines, start=1) if line.strip()]
    if not indexed_lines:
        return []

    chunks: list[ChunkRecord] = []
    start = 0
    step = chunk_size - overlap

    while start < len(indexed_lines):
        window = indexed_lines[start : start + chunk_size]
        text = "\n".join(line for _, line in window).strip()
        if text:
            payload = f"{document.source}:{start}:{text}".encode("utf-8")
            chunk_hash = hashlib.sha1(payload).hexdigest()[:12]
            metadata = {**document.metadata, "content_type": document.content_type}
            chunks.append(
                ChunkRecord(
                    chunk_id=f"{document.source}-{chunk_hash}",
                    source=document.source,
                    text=text,
                    line_start=window[0][0],
                    line_end=window[-1][0],
                    metadata=metadata,
                )
            )

        start += step

    return chunks
