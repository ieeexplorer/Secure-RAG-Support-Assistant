from app.rag.chunking import chunk_document
from app.rag.types import SourceDocument


def test_chunk_document_preserves_line_ranges() -> None:
    document = SourceDocument(
        source="sample.md",
        text="line1\nline2\nline3\nline4\nline5",
        content_type="md",
        lines=["line1", "line2", "line3", "line4", "line5"],
    )

    chunks = chunk_document(document, chunk_size=3, overlap=1)

    assert len(chunks) == 3
    assert chunks[0].line_start == 1
    assert chunks[0].line_end == 3
    assert chunks[1].line_start == 3
    assert chunks[1].line_end == 5
