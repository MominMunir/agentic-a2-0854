# Reproducible measurements

| Variant | Recall@5 | MRR | nDCG@10 | Retrieval p95 (s) |
| --- | --- | --- | --- | --- |
| v0 | 0.996 | 1.000 | 0.999 | 0.040 |
| v1 | 1.000 | 1.000 | 1.000 | 0.096 |
| v2 | 0.310 | 0.667 | 0.592 | 0.041 |
| v3 | 0.204 | 0.984 | 0.567 | 0.287 |
| v4 | 0.259 | 0.635 | 0.505 | 0.030 |
| v8 | 0.310 | 0.667 | 0.592 | 0.032 |

Source: `evals/results/retrieval.json`; synthetic domain holdout, actual open CPU models.

| Toolset | Tasks | Selection accuracy | Argument accuracy | Amortized tokens/task |
| --- | --- | --- | --- | --- |
| fine | 40 | 1.000 | 1.000 | 50.4 |
| coarse | 40 | 1.000 | 1.000 | 55.5 |
| rewritten | 40 | 1.000 | 0.800 | 52.8 |

Source: `evals/results/tool_study.json`; actual Groq inference, batched synthetic tasks.

| Architecture | Attempted | Completed | Decision accuracy* | Unsupported before/draft | p95 (s) |
| --- | --- | --- | --- | --- | --- |
| react | 50 | 49 | 0.920 | 6.472 | 27.38 |
| supervisor | 50 | 1 | 0.020 | n/a (no drafts) | 0.24 |
| handwritten | 50 | 12 | 0.240 | n/a (no drafts) | 36.09 |
| handwritten_alt | 50 | 20 | 0.400 | 1.133 | 51.94 |

Source: `evals/results/orchestration.json`. *Accuracy denominator is specified in the source summary. Failed attempts remain visible. Reply/hire rates unavailable without instructor GigSim.
