from dataclasses import dataclass, field


@dataclass(slots=True)
class SourceDocument:
    source: str
    text: str
    content_type: str
    lines: list[str]
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    source: str
    text: str
    line_start: int | None
    line_end: int | None
    metadata: dict[str, str]
