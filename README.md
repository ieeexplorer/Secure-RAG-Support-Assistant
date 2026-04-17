# secure-rag-support-assistant

A production-style RAG assistant that answers support questions from a private knowledge base, returns grounded responses with citations, evaluates answer quality, and optionally exposes safe support tools over MCP.

## What it includes

- FastAPI service for ingestion, question answering, and evaluation
- FastAPI authentication with an `X-API-Key` header for demo routes
- Structured request logging with an `X-Request-ID` response header
- Chroma-backed semantic retrieval over Markdown, PDF, TXT, and CSV sources
- Citation-aware answers with source names and line ranges
- Heuristic evaluation for relevance, faithfulness, and retrieval hit rate
- Optional MCP server with allowlisted support tools
- Streamlit UI with a cleaner operator-style demo layout
- Docker support and sample support knowledge base content

## Architecture

1. Documents are loaded from the knowledge base directory.
2. Each document is chunked into overlapping line-based passages.
3. Chunks are embedded and indexed in Chroma.
4. A query retrieves the most relevant passages.
5. The assistant answers with citations and a confidence estimate.
6. Evaluation scripts score answer quality on a small benchmark set.

## Project layout

```text
app/
  api/               FastAPI routes
  eval/              Evaluation metrics and runner
  rag/               Loaders, chunking, vector store, generation pipeline
  tools/             Allowlisted support tools
  ui/                Streamlit demo
data/
  eval/              Sample benchmark questions
  mock/              Mock tool backing data
knowledge_base/      Sample support documents
scripts/             CLI entrypoints for ingest and evaluation
tests/               Focused unit tests
```

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
```

The example values are dummy-safe defaults for local demos. LLM mode is disabled by default, so the dummy `OPENAI_API_KEY` is ignored unless you explicitly set `ENABLE_LLM=true` and replace it with a real key.

### 3. Ingest the knowledge base

```bash
python scripts/ingest_kb.py
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

### 5. Ask a question

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ask ^
  -H "X-API-Key: demo-support-token" ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"How do I reset MFA after a lost phone?\"}"
```

### 6. Run evaluation

```bash
python scripts/run_eval.py
```

### 7. Run the Streamlit demo

```bash
streamlit run app/ui/streamlit_app.py
```

### 8. Run the MCP server

```bash
python -m app.mcp_server
```

## API endpoints

- `GET /health` public health route
- `POST /api/v1/ingest` requires `X-API-Key`
- `POST /api/v1/ask` requires `X-API-Key`
- `POST /api/v1/evaluate` requires `X-API-Key`
- `GET /api/v1/tools/ticket/{ticket_id}` requires `X-API-Key`
- `GET /api/v1/tools/error/{error_code}` requires `X-API-Key`
- `POST /api/v1/tools/follow-up` requires `X-API-Key`

## Security posture

- API routes are protected with a shared demo secret for local testing.
- Tool access is explicit and allowlisted.
- Tool inputs are validated and constrained.
- Follow-up note creation writes only to local mock data used for demos.
- The assistant returns a fallback response when evidence is weak rather than overclaiming.
- Every response includes an `X-Request-ID` header for traceability.

## Dummy demo data

- The repo includes a dummy support corpus covering MFA, VPN, onboarding, device replacement, and AWS sandbox access.
- Mock ticket and error-code data back the safe tools so the workflow is testable with no external systems.
- The local config values are non-secret placeholders designed for extractive-mode demos.

## Example response shape

```json
{
  "answer": "To reset MFA after a lost phone, open the helpdesk portal and request an identity verification reset from the IAM team. A temporary bypass code is valid for 24 hours. [remote_access_policy.md lines 11-18]",
  "citations": [
    {
      "source": "remote_access_policy.md",
      "line_start": 11,
      "line_end": 18,
      "snippet": "If an employee loses a device..."
    }
  ],
  "confidence": 0.77,
  "evaluation": {
    "relevance": 0.82,
    "faithfulness": 0.89,
    "retrieval_hit": 1.0
  },
  "fallback_used": false
}
```

## Recommended next extensions

- Replace the dummy knowledge base with internal support content
- Swap shared-header auth for a real identity provider or signed service tokens
- Swap Chroma for pgvector if PostgreSQL is already in use
- Add LangSmith, MLflow, or OpenTelemetry tracing for deeper observability

