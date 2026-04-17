from __future__ import annotations

import json
from pathlib import Path

from app.eval.metrics import faithfulness_score, relevance_score, retrieval_hit_score
from app.schemas import DatasetEvaluationResponse, EvalSample


def run_evaluation(assistant, dataset_path: Path) -> DatasetEvaluationResponse:
    samples = [EvalSample.model_validate(item) for item in json.loads(dataset_path.read_text(encoding="utf-8"))]

    details: list[dict] = []
    relevance_values: list[float] = []
    faithfulness_values: list[float] = []
    retrieval_values: list[float] = []

    for sample in samples:
        result = assistant.answer(sample.question)
        metrics = {
            "relevance": relevance_score(sample.question, result.answer),
            "faithfulness": faithfulness_score(result.answer, result.retrieved_context),
            "retrieval_hit": retrieval_hit_score(sample.expected_doc, [citation.model_dump() for citation in result.citations]),
        }

        if sample.must_include:
            included = sum(1 for term in sample.must_include if term.lower() in result.answer.lower())
            metrics["must_include_coverage"] = round(included / len(sample.must_include), 4)

        relevance_values.append(metrics["relevance"])
        faithfulness_values.append(metrics["faithfulness"])
        retrieval_values.append(metrics["retrieval_hit"])
        details.append(
            {
                "question": sample.question,
                "answer": result.answer,
                "citations": [citation.model_dump() for citation in result.citations],
                **metrics,
            }
        )

    sample_count = len(samples)
    return DatasetEvaluationResponse(
        sample_count=sample_count,
        average_relevance=round(sum(relevance_values) / sample_count, 4) if sample_count else 0.0,
        average_faithfulness=round(sum(faithfulness_values) / sample_count, 4) if sample_count else 0.0,
        average_retrieval_hit=round(sum(retrieval_values) / sample_count, 4) if sample_count else 0.0,
        details=details,
    )
