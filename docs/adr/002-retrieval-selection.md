# Retrieval selection

Status: accepted. Recorded 15 November 2026.

Ship V0 dense retrieval after selecting on development Recall@5, nDCG@10 and
latency. Keep V1, V2, V3, V4 and V8 available for reproducible comparisons.
The frozen domain holdout is used only for reporting.

Advanced stages did not improve this synthetic corpus. Template-derived labels
limit generalization. Evidence: `evals/results/retrieval.json` and
`evaluation/raw/retrieval.jsonl`.
