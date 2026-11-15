# GigBid execution plan and requirement ledger

Prepared 2026-11-15 after reading all 14 pages of the assignment. The original
starter kit remains unchanged and is reference material only. No instructor
GigSim service, full persona corpus, dev labels, hidden set or November 2 policy
update was supplied. Local substitutes must be labeled and never reported as
instructor or hidden-test results. At planning time only the original November 12
deadline was known. Update: the owner subsequently confirmed an extension to
midnight PKT at the end of November 15, 2026. Commit timestamps remain unaltered.

## Architecture and implementation sequence

1. Foundation: pinned Python package, React/TypeScript web client, configuration,
   SQL persistence, authentication, encrypted OAuth store, secret-free templates.
2. Data: provenance-preserving Kaggle import, deterministic synthetic personas,
   clients, reviews, proposals, conversations, adversarial jobs and dev labels.
   Keep real and synthetic files separate. Preserve raw archives outside releases.
3. MCP: official SDK Portfolio, Marketplace and Workspace servers; tool schemas,
   tenant-scoped authentication, idempotency, dry runs, append-only redacted audit;
   per-role MultiServerMCPClient allowlists and bounded retries. A separate local
   simulator is a substitute, never an alteration of the missing gigsim package.
4. Retrieval: loaders, incremental chunks, open dense embeddings and reranker;
   V0 dense, V1 decomposition, V2 BM25/dense RRF, V3 cross-encoder, V8 corrective
   retrieval, optional outcome boost. Evaluate all components without conflating
   CPU lexical smoke measurements with open-model measurements.
5. Graphs: handwritten StateGraphs with Send fan-out, typed handoffs, bounded
   critique, claim verification, compliance, human interrupt, durable checkpoint,
   exactly-once approved effects; separate conversation graph and two memory
   namespaces governed by promotion rules. Open model nodes use versioned prompts.
6. API/worker/UI: Redis worker and saved-search scheduler; authenticated API,
   persisted run events/SSE; nine responsive screens and generated OpenAPI types;
   approval/editor, evidence matrix, messages, analytics, settings/memory viewer.
7. Verification: unit, in-memory MCP/schema contracts, graph/HTTP integration,
   crash/restart/idempotency, cross-tenant isolation and Playwright user journeys.
8. Research: pre-registered hypotheses, raw observations, per-persona metrics,
   ablations, tool-study and orchestration runners, human/judge annotation packets.
   Record missing experiments as pending, never fabricate labels, tokens or costs.
9. Delivery: compose with Postgres/Redis/Qdrant/Ollama/Phoenix, deployment runbook,
   report <=10 pages, 1,200-1,800 word article, demo script, clean archive and
   environment-generated reviewer credentials kept only in ignored private files.

## Grading traceability

| Requirements | Concrete components | Verification / evidence |
|---|---|---|
| R1, A4 | marketplace_port; GigSim and Upwork adapters; OAuth PKCE encrypted tokens | adapter contracts; live tests require user's account |
| R2, A1-A3, A5-A7 | 3 SDK servers; Portfolio resources/prompts; GitHub remote MCP | MCP SDK sessions, schema snapshot, Inspector procedure |
| R3, C1-C4 | bid/conversation StateGraphs; analyst/risk/fit Send branches; Pydantic handoffs | graph diagrams, routing and bounded-loop tests |
| R4, C5-C7 | interrupt approval, Postgres checkpoints, idempotency ledger, retries | restart/resume, reject/edit and double-submit tests |
| R5, B3 | atomic claims with evidence references, verifier and rechecked edits | unsupported rate before/after; adversarial claims |
| R6, B1-B5 | V0/V1/V2/V3/V8, metadata loaders, reproducible evaluation | Recall@5, MRR, nDCG@10; per persona/job type; ablation |
| R7, C2 | LangGraph style/outcome store and explicit promotion | promotion/delete/isolation tests; edit diffs |
| R8, E3/E5 | trace propagation, PII redaction, token/step budgets, Phoenix | p50/p95, per-node actual usage and cost records |
| R9, E1/E4 | untrusted text boundaries; policy config; Redis scheduler; rate limits | injection ASR, outage/recovery, no auto-send tests |
| R10, D, E6 | React+TS/FastAPI, reviewer auth, compose | E2E onboarding/approve/reject/edit/outage; deploy checklist |
| D screens | signin/onboard, inbox/detail, studio, pipeline, messages, runs, analytics, settings | responsive screenshots and Playwright report |
| E2 | CI tests, smoke evaluation, schema/secrets/source checks | threshold gates; evals/results plus evaluation raw files |
| Research A (40 tasks) | fine/coarse/rewritten tool study | actual Groq selection/arguments/tokens in tool_study.json |
| Research B | preregistered retrieval hypothesis and component comparisons | synthetic relevance and unsupported claims measured; human/judge calibration not conducted |
| Research C (50 attempts per design) | ReAct/prebuilt-supervisor/handwritten runners | retained accuracy/usage/latency; unequal quota failures prevent fair ranking |
| Models | 2 hosted open configurations, CPU embeddings/reranker | actual returned usage and client latency; local LLM throughput not measured |
| X1 | agency mode across three synthetic profiles | routing accuracy and evidence/persona isolation |
| Deliverables | README, report, article, demo, Docker MCP install, résumé bullets | links to actual result files; packaging manifest |

## Declared budgets and hypotheses (before experiments)

For local open inference: p95 job analysis <=60 seconds; p95 proposal <=120
seconds; max 12,000 tokens and 35 graph steps per thread; max two Writer revisions;
API inference spend ceiling USD 0.05/job and USD 0.10/proposal. CPU smoke runs
are measured separately and do not establish these open-model budgets.

H-A: rewritten, focused tool descriptions improve selection accuracy over an
ambiguous coarse toolset on 40 labeled tasks.

H-B: requirement decomposition plus hybrid retrieval improves Recall@5 over V0
on multi-requirement jobs; reranking may trade latency for precision. Use an
explicit development/holdout split before selecting a deployment variant.

H-C: isolated analysis roles reduce unsupported claims and compliance failures
relative to a single agent, with additional latency and token cost.

## External checkpoints

- Ask for instructor assets and open-model endpoint; continue independent work.
- Authenticate Upwork/GitHub only with the user's account authorization.
- Prepare deployments locally; ask before external cloud deployment commands.
- Public URLs, real GigSim outcomes, blind human-panel labels, judge calibration,
  the actual policy change, hidden results, and a recorded/published video cannot
  be asserted without the respective external input or action.

## Final implementation evidence

The initial plan above remains as the pre-experiment record. The final local
build passed 35 backend tests and six browser journeys. Real Groq inference was
used for the 40-task/toolset study and 200 architecture attempts; daily quotas
prevent a fair architecture ranking. Retrieval covers six variants and 180
queries, with V0 selected only on development. Official MCP Inspector captures,
an isolated wheel check, a real Postgres restart check, and a 512 MiB compact
deployment test are saved. After a cloud sign-in memory failure, the compact
runtime was revised and the regression check peaked at 432.22 MiB. Public app,
MCP, Neon and Qdrant checks passed; see docs/DEPLOYMENT_STATUS.md. Independent
human calibration, instructor assets/outcomes and separate blog/video publication
remain external work; 30 real drafts and 14 blind pairs are prepared for raters.
