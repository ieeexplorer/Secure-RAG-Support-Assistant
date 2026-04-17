from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    line_start: int | None = None
    line_end: int | None = None
    snippet: str


class EvaluationSummary(BaseModel):
    relevance: float = Field(ge=0.0, le=1.0)
    faithfulness: float = Field(ge=0.0, le=1.0)
    retrieval_hit: float = Field(ge=0.0, le=1.0)


class AnswerRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=10)


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    evaluation: EvaluationSummary
    fallback_used: bool = False
    retrieved_context: list[dict[str, Any]] = Field(default_factory=list)


class IngestRequest(BaseModel):
    source_dir: str | None = None
    rebuild: bool = False


class IngestResponse(BaseModel):
    source_dir: str
    indexed_documents: int
    indexed_chunks: int


class EvalSample(BaseModel):
    question: str
    expected_doc: str | None = None
    must_include: list[str] = Field(default_factory=list)


class DatasetEvaluationResponse(BaseModel):
    sample_count: int
    average_relevance: float
    average_faithfulness: float
    average_retrieval_hit: float
    details: list[dict[str, Any]]


class FollowUpNoteRequest(BaseModel):
    ticket_id: str
    note: str = Field(min_length=5, max_length=500)
    author: str = Field(default="assistant", min_length=2, max_length=50)
