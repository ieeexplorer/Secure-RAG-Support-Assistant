from __future__ import annotations

import re


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) > 2}


def relevance_score(question: str, answer: str) -> float:
    q_tokens = _tokenize(question)
    a_tokens = _tokenize(answer)
    if not q_tokens:
        return 0.0
    return round(len(q_tokens & a_tokens) / len(q_tokens), 4)


def faithfulness_score(answer: str, retrieved_context: list[dict]) -> float:
    answer_tokens = _tokenize(answer)
    context_tokens = _tokenize(" ".join(item["text"] for item in retrieved_context))
    if not answer_tokens:
        return 0.0
    return round(len(answer_tokens & context_tokens) / len(answer_tokens), 4)


def retrieval_hit_score(expected_doc: str | None, citations: list[dict]) -> float:
    if not expected_doc:
        return 1.0
    normalized = expected_doc.lower()
    return 1.0 if any(item["source"].lower() == normalized for item in citations) else 0.0
