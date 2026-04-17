from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import streamlit as st

from app.config import Settings, get_settings
from app.rag.pipeline import RAGAssistant
from app.schemas import AnswerResponse
from app.tools.support_tools import SupportToolService


st.set_page_config(page_title="Secure RAG Support Assistant", page_icon="S", layout="wide")


@st.cache_resource
def load_settings() -> Settings:
    return get_settings()


@st.cache_resource
def load_assistant() -> RAGAssistant:
    assistant = RAGAssistant(load_settings())
    assistant.ingest(rebuild=False)
    return assistant


@st.cache_resource
def load_tool_service() -> SupportToolService:
    return SupportToolService(data_dir=load_settings().mock_data_dir)


@st.cache_data
def load_stylesheet() -> str:
    css_path = Path(__file__).with_name("styles.css")
    return css_path.read_text(encoding="utf-8")


@st.cache_data
def load_corpus_preview(base_dir: Path) -> list[tuple[str, str]]:
    previews: list[tuple[str, str]] = []
    for path in sorted(base_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".csv"}:
            continue
        preview = path.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
        previews.append((path.name, "\n".join(preview[:8])))
    return previews


def render_shell_open() -> None:
    st.markdown('<div class="demo-shell">', unsafe_allow_html=True)


def render_shell_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_metric_card(label: str, value: str, tone: str = "neutral") -> None:
    st.markdown(
        (
            f'<div class="metric-card {tone}">'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_response(response: AnswerResponse) -> None:
    tone = "strong" if response.confidence >= 0.7 and not response.fallback_used else "caution"
    status = "Strong grounding" if tone == "strong" else "Needs review"

    st.markdown(
        (
            f'<div class="answer-card {tone}">'
            f'<div class="answer-eyebrow">{status}</div>'
            f'<div class="answer-body">{response.answer}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(4)
    with metric_columns[0]:
        render_metric_card("Confidence", f"{response.confidence:.2f}", tone)
    with metric_columns[1]:
        render_metric_card("Relevance", f"{response.evaluation.relevance:.2f}")
    with metric_columns[2]:
        render_metric_card("Faithfulness", f"{response.evaluation.faithfulness:.2f}")
    with metric_columns[3]:
        render_metric_card("Fallback", "yes" if response.fallback_used else "no")

    st.subheader("Citations")
    for citation in response.citations:
        with st.expander(f"{citation.source} | lines {citation.line_start}-{citation.line_end}"):
            st.write(citation.snippet)

    with st.expander("Retrieved context"):
        st.json(response.retrieved_context)


def render_tool_panel(tool_service: SupportToolService) -> None:
    tickets = tool_service.list_tickets()
    errors = tool_service.list_error_codes()

    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Ticket status")
        ticket_ids = [ticket["ticket_id"] for ticket in tickets]
        selected_ticket = st.selectbox("Choose a ticket", ticket_ids, key="ticket_lookup")
        if selected_ticket is not None and st.button("Lookup ticket", use_container_width=True):
            st.json(tool_service.search_ticket_status(selected_ticket))

        st.subheader("Create follow-up note")
        with st.form("follow_up_form"):
            follow_up_ticket = st.selectbox("Ticket", ticket_ids, key="follow_up_ticket")
            follow_up_author = st.text_input("Author", value="assistant")
            follow_up_note = st.text_area("Note", height=120, placeholder="Add a concise support note.")
            submitted = st.form_submit_button("Create note", use_container_width=True)
            if submitted and follow_up_ticket is not None:
                result = tool_service.create_followup_note(follow_up_ticket, follow_up_note, follow_up_author)
                st.success(f"Created note on {result['ticket_id']}.")
                st.json(result)

    with right_column:
        st.subheader("Error code lookup")
        error_codes = [error["error_code"] for error in errors]
        selected_error = st.selectbox("Choose an error code", error_codes, key="error_lookup")
        if selected_error is not None and st.button("Lookup error", use_container_width=True):
            st.json(tool_service.lookup_error_code(selected_error))

        st.subheader("Allowlisted tools")
        st.write(sorted(tool_service.allowed_tools))


def main() -> None:
    settings = load_settings()
    assistant = load_assistant()
    tool_service = load_tool_service()

    if "question_input" not in st.session_state:
        st.session_state.question_input = "How do I reset MFA after losing my phone?"
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None

    history = cast(list[dict[str, Any]], st.session_state["history"])
    last_response = cast(AnswerResponse | None, st.session_state["last_response"])

    st.markdown(f"<style>{load_stylesheet()}</style>", unsafe_allow_html=True)

    corpus_preview = load_corpus_preview(settings.knowledge_base_dir)

    with st.sidebar:
        render_shell_open()
        st.markdown("### Demo Controls")
        st.caption("Protected API header")
        st.code("X-API-Key: demo-support-token")
        st.caption("LLM mode")
        st.write("Disabled by default so the demo runs on dummy local config.")
        st.caption("Knowledge base")
        st.write(f"{len(corpus_preview)} demo documents ready for retrieval.")
        if st.button("Rebuild demo index", use_container_width=True):
            result = assistant.ingest(rebuild=True)
            st.success(f"Indexed {result.indexed_documents} documents and {result.indexed_chunks} chunks.")
        render_shell_close()

    st.markdown(
        """
        <div class="hero-panel">
          <div class="hero-kicker">Secure retrieval demo</div>
          <h1>Support answers with citations, request IDs, and safe tool boundaries.</h1>
          <p>
            This demo runs on dummy helpdesk content, protects API routes with a shared header,
            and surfaces evaluation signals so weak evidence is visible instead of hidden.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prompt_columns = st.columns(4)
    sample_prompts = [
        ("Lost MFA device", "How do I reset MFA after losing my phone?"),
        ("VPN error 742", "What should I do when VPN error 742 appears?"),
        ("Battery swelling", "What is the process for a swollen laptop battery?"),
        ("AWS sandbox", "When is AWS sandbox access approved for new users?"),
    ]
    for column, (label, prompt) in zip(prompt_columns, sample_prompts, strict=False):
        if column.button(label, use_container_width=True):
            st.session_state.question_input = prompt

    assistant_tab, tools_tab, corpus_tab = st.tabs(["Assistant", "Tool Sandbox", "Corpus"])

    with assistant_tab:
        render_shell_open()
        with st.form("ask_form"):
            question = st.text_area("Ask a support question", key="question_input", height=120)
            top_k = st.slider("Retrieved passages", min_value=1, max_value=6, value=settings.top_k)
            submitted = st.form_submit_button("Run grounded answer", use_container_width=True)

        if submitted and question.strip():
            response = assistant.answer(question=question.strip(), top_k=top_k)
            st.session_state.last_response = response
            history.append({"question": question.strip(), "confidence": response.confidence})
            last_response = response

        if last_response is not None:
            render_response(last_response)

        if history:
            with st.expander("Recent demo questions"):
                for item in reversed(history[-5:]):
                    st.write(f"{item['question']} | confidence {item['confidence']:.2f}")
        render_shell_close()

    with tools_tab:
        render_shell_open()
        render_tool_panel(tool_service)
        render_shell_close()

    with corpus_tab:
        render_shell_open()
        st.subheader("Dummy corpus preview")
        for name, preview in corpus_preview:
            with st.expander(name):
                st.text(preview)
        render_shell_close()


main()

