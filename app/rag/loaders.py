from __future__ import annotations

import csv
from pathlib import Path

from pypdf import PdfReader

from app.rag.types import SourceDocument


SUPPORTED_EXTENSIONS = {".md", ".txt", ".csv", ".pdf"}


def _read_text_file(path: Path) -> SourceDocument:
    text = path.read_text(encoding="utf-8")
    return SourceDocument(
        source=path.name,
        text=text,
        content_type=path.suffix.lstrip("."),
        lines=text.splitlines(),
    )


def _read_csv_file(path: Path) -> SourceDocument:
    rows: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            rendered = " | ".join(f"{key}: {value}" for key, value in row.items())
            rows.append(f"Row {index}: {rendered}")

    text = "\n".join(rows)
    return SourceDocument(
        source=path.name,
        text=text,
        content_type="csv",
        lines=text.splitlines(),
    )


def _read_pdf_file(path: Path) -> SourceDocument:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text() or ""
        pages.append(f"Page {page_number}\n{extracted.strip()}")

    text = "\n\n".join(pages)
    return SourceDocument(
        source=path.name,
        text=text,
        content_type="pdf",
        lines=text.splitlines(),
    )


def load_documents(source_dir: Path) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        suffix = path.suffix.lower()
        if suffix in {".md", ".txt"}:
            documents.append(_read_text_file(path))
        elif suffix == ".csv":
            documents.append(_read_csv_file(path))
        elif suffix == ".pdf":
            documents.append(_read_pdf_file(path))

    return documents
