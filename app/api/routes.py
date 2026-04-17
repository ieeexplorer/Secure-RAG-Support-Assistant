from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from app.config import get_settings
from app.eval.runner import run_evaluation
from app.observability import configure_observability
from app.rag.pipeline import RAGAssistant
from app.schemas import (
    AnswerRequest,
    AnswerResponse,
    DatasetEvaluationResponse,
    FollowUpNoteRequest,
    IngestRequest,
    IngestResponse,
)
from app.security import require_api_key
from app.tools.support_tools import SupportToolService


router = APIRouter(prefix="/api/v1", tags=["rag"], dependencies=[Depends(require_api_key)])


@lru_cache(maxsize=1)
def get_assistant() -> RAGAssistant:
    return RAGAssistant(get_settings())


@lru_cache(maxsize=1)
def get_tool_service() -> SupportToolService:
    return SupportToolService(data_dir=get_settings().mock_data_dir)


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(request: IngestRequest) -> IngestResponse:
    source_dir = Path(request.source_dir) if request.source_dir else None
    return get_assistant().ingest(source_dir=source_dir, rebuild=request.rebuild)


@router.post("/ask", response_model=AnswerResponse)
def ask_question(request: AnswerRequest) -> AnswerResponse:
    return get_assistant().answer(question=request.question, top_k=request.top_k)


@router.post("/evaluate", response_model=DatasetEvaluationResponse)
def evaluate_dataset() -> DatasetEvaluationResponse:
    dataset_path = Path("data/eval/questions.json")
    return run_evaluation(get_assistant(), dataset_path)


@router.get("/tools/ticket/{ticket_id}")
def search_ticket_status(ticket_id: str) -> dict:
    try:
        return get_tool_service().search_ticket_status(ticket_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tools/error/{error_code}")
def lookup_error_code(error_code: str) -> dict:
    try:
        return get_tool_service().lookup_error_code(error_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tools/follow-up")
def create_followup_note(request: FollowUpNoteRequest) -> dict:
    try:
        return get_tool_service().create_followup_note(
            ticket_id=request.ticket_id,
            note=request.note,
            author=request.author,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.service_name, version="0.2.0")
    configure_observability(app, settings)

    @app.get("/health", tags=["system"])
    def healthcheck() -> dict[str, str | bool]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "auth_enabled": settings.api_auth_enabled,
        }

    app.include_router(router)
    return app
