from __future__ import annotations

import re
from typing import Any

from openai import OpenAI

from app.config import Settings


STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "before",
    "can",
    "could",
    "does",
    "during",
    "for",
    "from",
    "have",
    "how",
    "into",
    "must",
    "should",
    "that",
    "the",
    "their",
    "them",
    "then",
    "they",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
    "within",
    "would",
    "your",
}


class AnswerGenerator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_enabled else None

    def generate(self, question: str, retrieved_chunks: list[dict[str, Any]]) -> tuple[str, bool]:
        if not retrieved_chunks:
            return (
                "I could not find enough evidence in the knowledge base to answer that safely. Please refine the question or ingest more support documentation.",
                True,
            )

        if self._client is not None:
            return self._generate_with_llm(question, retrieved_chunks), False
        return self._generate_extractive(question, retrieved_chunks), False

    def _generate_with_llm(self, question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
        context_blocks = []
        for chunk in retrieved_chunks:
            metadata = chunk["metadata"]
            context_blocks.append(
                f"Source: {metadata.get('source')} lines {metadata.get('line_start')}-{metadata.get('line_end')}\n{chunk['text']}"
            )

        prompt = (
            "Answer the support question using only the evidence below. "
            "If evidence is weak, explicitly say so. Include inline citations using the format "
            "[source lines X-Y].\n\n"
            f"Question: {question}\n\n"
            f"Evidence:\n\n{chr(10).join(context_blocks)}"
        )
        response = self._client.responses.create(model=self._settings.openai_model, input=prompt)
        return response.output_text.strip()

    def _generate_extractive(self, question: str, retrieved_chunks: list[dict[str, Any]]) -> str:
        selected_chunks = select_relevant_chunks(question, retrieved_chunks)
        query_terms = _tokenize(question)
        evidence_lines: list[str] = []

        for chunk in selected_chunks:
            best_sentence = max(
                _split_sentences(chunk["text"]),
                key=lambda sentence: _overlap_score(sentence, query_terms),
                default=chunk["text"],
            )
            best_sentence = _clean_sentence(best_sentence)
            metadata = chunk["metadata"]
            rendered = f"{best_sentence.strip()} [{metadata.get('source')} lines {metadata.get('line_start')}-{metadata.get('line_end')}]"
            if rendered not in evidence_lines:
                evidence_lines.append(rendered)

        intro = "Based on the retrieved support documentation, the strongest evidence is:"
        return "\n".join([intro, *evidence_lines])


def _split_sentences(text: str) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return sentences or [text]


def _overlap_score(text: str, query_terms: set[str]) -> int:
    tokens = _tokenize(text)
    return len(tokens & query_terms)


def select_relevant_chunks(question: str, retrieved_chunks: list[dict[str, Any]], max_chunks: int = 2) -> list[dict[str, Any]]:
    if not retrieved_chunks:
        return []

    query_terms = _tokenize(question)
    scored_chunks = []
    for chunk in retrieved_chunks:
        overlap = _overlap_score(chunk["text"], query_terms)
        blended_score = (chunk["score"] * 0.7) + (min(overlap, 4) / 4 * 0.3)
        scored_chunks.append((blended_score, overlap, chunk))

    scored_chunks.sort(key=lambda item: (item[0], item[1]), reverse=True)
    best_score = scored_chunks[0][0]
    selected = [item[2] for item in scored_chunks if item[0] >= max(best_score * 0.75, 0.35) and item[1] > 0]
    if not selected:
        selected = [scored_chunks[0][2]]
    return selected[:max_chunks]


def _clean_sentence(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text.strip())
    return text.lstrip("| ")


def _normalize_token(token: str) -> str:
    overrides = {
        "login": "log",
        "logged": "log",
        "swollen": "swell",
        "swelling": "swell",
    }
    token = overrides.get(token, token)
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token


def _tokenize(text: str) -> set[str]:
    tokens = set()
    for raw_token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
        if len(raw_token) <= 2 or raw_token in STOPWORDS:
            continue
        tokens.add(_normalize_token(raw_token))
    return tokens
