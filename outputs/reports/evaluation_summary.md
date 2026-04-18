# Evaluation Summary

Generated from `python scripts/run_eval.py` on 2026-04-18 using the bundled knowledge base, local extractive mode, and the sample dataset in `data/eval/questions.json`.

## Headline Metrics

| Metric | Value | Readout |
| --- | ---: | --- |
| Sample count | 6 | Small but useful demo benchmark. |
| Average relevance | 0.5669 | Answer shaping is the main improvement area. |
| Average faithfulness | 0.7406 | Most answers stay grounded in retrieved evidence. |
| Average retrieval hit | 1.0000 | The expected source document was surfaced for every sample. |

## What This Snapshot Shows

- Retrieval is working well on the bundled support corpus.
- The main weakness is answer compression, especially when CSV rows introduce extra context.
- This repo already has a measurable baseline, which makes future tuning easy to justify and compare.

## Representative Cases

- MFA reset after device loss: correct source documents were cited and the answer stayed grounded.
- VPN error 742: retrieval found the right source, but extractive mode included extra CSV context that lowered relevance.
- AWS sandbox approval timing: concise answer with the correct source citation.

## Raw Artifact

The full benchmark output is committed in `outputs/reports/evaluation_snapshot.json`.