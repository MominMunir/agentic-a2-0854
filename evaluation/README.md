# Evaluation evidence

All records identify synthetic fixtures, real historical data, or actual model calls.
Synthetic gold is template derived, not independent human judgment. Real Kaggle
jobs inform historical pricing and demonstrate preprocessing; they do not supply
freelancer claims, fabricated outcomes, or relevance labels.

| Evidence | Reproduction | Interpretation |
|---|---|---|
| `raw/retrieval.jsonl`, `retrieval_comparison.png` | `python -m evaluation.run` | Six variants, 180 queries; domain split; choose only on development |
| `raw/tool_study.jsonl` | `python -m evaluation.tool_study` | 40 tasks per toolset, actual Groq inference; tokens amortized across a batch |
| `raw/orchestration.jsonl` | `python -m evaluation.orchestration --limit 50` | 200 historical attempts; sequential groups and unequal provider quotas prevent a fair ranking |
| `raw/agency.jsonl` | `python -m evaluation.agency_eval` | 180 synthetic routing cases with actual embeddings/MCP |
| `raw/matching_repair.jsonl` | `python -m evaluation.matching_repair` | Frozen 50-case development diagnostic; both query modes scored 1.0, so no accuracy improvement claimed |
| `annotations/` | `python -m evaluation.human_panel prepare` | 30 actual drafts for calibration and available blind pairs; human labels remain blank |
| `pytest.xml`, `playwright.json` | `pytest`; frontend `npm run test:e2e` | Deterministic boundary/browser checks, separate from model quality |
| `python_audit.json`, `npm_audit.json` | See runbook/CI | Point-in-time dependency audits |
| `raw/free_deployment.jsonl` | `python -m scripts.free_deployment_smoke` | Local compact image under 512 MiB; no public deployment or always-on guarantee |

Canonical aggregates are in `../evals/results/`. `python -m evaluation.summarize`
recomputes architecture tables from raw attempts. Failed/invalid outputs count as
incorrect in all-attempt accuracy; completed-only accuracy is also available.
Claim rates use actual nonempty drafts; no drafts means unavailable. Latency p95
includes failures, with completed/draft latency separately recorded. Cost is a
public-list-price estimate from returned input/output token counts. Missing usage
on failed calls is unknown, not zero; this is not an invoice.

For publication, em dash punctuation in one recorded cover letter and its
annotation copies was normalized. The affected JSONL record carries a
`publication_text_normalization` note. Original text remains in prior Git
history; all scores, usage, latencies and cost observations are unchanged.

The recorded architecture benchmark uses legacy requirement queries and predates
the whole-job retrieval, source-freshness, Connects approval, and fallback fixes.
The runner retains `--match-query-mode legacy` to revisit that diagnostic behavior;
the final implementation includes subsequent reliability changes. Exact provider
outputs, latency and quota availability will differ on reruns. Production defaults
to the measured V0 retrieval winner and whole-job queries.

Instructor GigSim, full persona corpora, independent development labels, the
November 2 policy update and hidden set were unavailable. No instructor reply/hire
rates, human kappa, panel preference scores or hidden-test results are claimed.
Logs retain unsuccessful observations and are scrubbed of keys and account identifiers.
