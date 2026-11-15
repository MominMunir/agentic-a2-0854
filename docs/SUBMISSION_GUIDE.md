# GigBid: submission status and viva guide

Audited against all 14 pages of the assignment on November 15, 2026.
The owner confirmed the deadline was extended to midnight Pakistan time at the
end of November 15. The PDF's original November 12 date is superseded by that
reported extension. Push the final source and submit before tonight's cutoff.
This guide is an honest inventory, not a claim that every grading requirement is
complete. No instructor or hidden-test outcome has been invented.

## 1. What this assignment asks you to build

AI-4016 Assignment II is an individual research and development project called
**GigBid, a Multi-Agent Freelancer Copilot**. It assists a freelancer from finding
a suitable job through drafting a truthful proposal and handling a client reply.
The system must explain its decisions, cite portfolio evidence, obey budgets and
pause for a human before contacting a client or spending Connects.

The assignment is more than a website or an LLM prompt. It requires a working
product, controlled agent workflows, MCP tools, measured retrieval and agent
experiments, durable approvals, production engineering and a public portfolio.
The written work totals 100 marks; a live viva applies a multiplier from 0 to 1.
Being able to explain and modify the implementation is part of the assessment.

| Part | Marks | What it assesses |
|---|---:|---|
| A: MCP tool layer | 20 | Three servers, contracts, authentication, safe writes, adapters and a tool-design study |
| B: Advanced RAG | 20 | Baseline plus advanced variants, grounding, evaluation, calibration and a defensible retrieval choice |
| C: Multi-agent graphs | 25 | Parallel LangGraph analysis, critique, approvals, checkpoints, memory and architecture comparison |
| D: Web interface | 15 | Complete responsive workspace, streaming progress, evidence and working approval controls |
| E: Production engineering | 10 | Worker, scheduling, CI, tracing, guardrails, budgets and live deployment |
| Portfolio and report | 10 | README, demo, installable MCP, article, evidence and engineering review |

One signature extension is required. This implementation chose **X1 agency mode**,
which selects the best-supported member from three freelancer personas.

## 2. What we built and verified

### Product and interface

- Original implementation in this repository, using the supplied starter kit as
  a reference. The starter kit was left unchanged.
- React and TypeScript frontend with a FastAPI backend, sign-in/onboarding,
  portfolio upload, inbox, job details, proposal studio, pipeline, messages,
  agent-run viewer, analytics and settings.
- Requirement-to-evidence matrix, evidence hover/focus, draft editing, rejection
  reasons, dry-run previews, approval and streamed run events.
- Responsive desktop and phone views. The latest UI change increases text by
  2 px throughout, including small labels and mobile overrides.
- Generated TypeScript API client/types from FastAPI OpenAPI.

### Agent workflows

- A handwritten LangGraph bid graph fans out to Analyst, Risk Assessor and Fit
  Matcher, then joins their outputs before the bid/watch/skip decision.
- Pricing checks the project budget, user floor, Connects balance and weekly cap.
- Writer drafts from retrieved evidence. Verifier removes unsupported claims.
  Critic can request at most two revisions. Compliance and budget checks run
  before a dry run and a durable human interrupt.
- A separate conversation graph drafts responses and suggests interview slots,
  verifies the draft and pauses before sending.
- These are software roles and graph nodes, not separately trained models.
  Some nodes use LLMs; fit scoring, budgets, approval checks and several safety
  rules deliberately use deterministic code.

### Tools, storage and safety

- Three MCP SDK servers: Portfolio for evidence; Marketplace for marketplace
  reads and controlled writes; Workspace for local calendar slots/holds and
  email drafts. Local Workspace mocks are permitted by the specification.
- One marketplace port with local simulator, instructor-GigSim adapter and
  official Upwork MCP/OAuth adapter. Actual instructor/live integration remains
  unverified; the public demo currently uses the labeled local simulator.
- Role-specific tool allowlists, tenant isolation, server-scoped bearer tokens,
  encrypted OAuth storage, rate limits and redacted audit events.
- Approval binds to the user, action, exact content, screening answers and
  Connects cost. Changed content/cost requires fresh approval. Deleted evidence
  is rechecked before a proposal can be approved.
- Idempotency ledger prevents duplicate local-simulator effects and wallet
  debits. A real upstream service still needs its own idempotency/reconciliation
  contract; local exactly-once tests do not prove external exactly-once behavior.
- Postgres checkpoints preserve pending work. Long-term style/outcome memories
  have explicit promotion rules and can be viewed/deleted in settings.

### Retrieval, data and models

- Six implemented/evaluated RAG variants: V0 dense, V1 decomposition, V2 hybrid
  BM25/dense fusion, V3 reranking, V4 outcome boost and V8 corrective retrieval.
- Open CPU BGE-small embeddings, FlashRank reranking, Qdrant storage and a local
  NumPy reference backend; metadata and incremental ingestion for supported
  document/code formats.
- Two approved Kaggle datasets actually imported: 1,000 normalized historical
  fixed-price jobs in total. Download/preprocessing code, manifest and licenses
  are documented. The other four approved datasets were not used.
- Separately tagged synthetic evidence: three personas, 330 evidence items,
  180 jobs and clients, 495 proposal-history records, 54 reviews and three
  conversations. The 330-item retrieval corpus includes only a subset of those
  proposal histories. These are generated fixtures, not instructor data.
- Groq hosts the open models: gpt-oss-20b for cheaper reasoning nodes and
  gpt-oss-120b for writing/critique; an alternate all-20b profile was compared.
  Ollama remains an optional configuration, not an installed local dependency
  or a claim of measured local LLM throughput.
- Historical jobs can inform advisory pricing locally. The public synthetic
  deployment discloses its fallback to the posted budget midpoint when no
  comparable historical data is present.

### Engineering and deployment

- Redis/Arq background work, saved-search schedules, bounded retries, fallback,
  recovery/dead-letter handling and queue locks.
- Full Docker Compose stack and a compact free deployment. The free profile
  shares the queue worker with the API process to fit memory; graph work still
  runs as a background worker task, outside the HTTP request.
- A cloud sign-in memory failure was reproduced and repaired. The revised
  local 512 MiB regression check peaked at 432.22 MiB.
- Public GitHub repository and GitHub Actions test/evaluation workflows.
- 35 backend tests passed in the existing final verification; all six browser
  journeys passed again after the font change. Those checks cover boundaries
  and workflows; they do not establish human-rated proposal quality.
- Real MCP Inspector captures, standalone wheel installation check, Postgres
  restart evidence and public authenticated MCP/storage checks are saved.
- Render web and Key Value, Neon and Qdrant were all verified on Free plans.

## 3. Research we actually ran, and what it means

| Study | Actual evidence | Conclusion and limit |
|---|---|---|
| Retrieval | Six variants on 180 frozen synthetic queries, with development/holdout domain split | Development selection chose V0. Its holdout Recall@5 was 0.996. Synthetic relevance is template-derived, not independent human gold. |
| Tool design | 40 known-call tasks for each of three toolsets, actual Groq inference | Selection was 1.0 for all; rewritten descriptions reduced argument accuracy to 0.8. Tasks were batched, so token/task figures are amortized. |
| Agent architecture | 50 attempts each for ReAct, prebuilt supervisor, handwritten graph and alternate graph profile | 200 real attempts, but unequal daily quotas caused many failures. This is not a fair architecture ranking or proof that more agents are better. |
| Agency extension | 180 synthetic routing cases with actual retrieval/MCP | Accuracy 1.0 on these fixtures; no real hiring or collaboration claim follows. |
| Decisions and injection rules | Synthetic rule-level smoke metrics and five claim challenges | Useful boundary checks; not an undefended-versus-defended LLM injection benchmark. |
| Public deployment | Actual Groq draft, reviewer login, scoped MCP, Neon checkpoints and Qdrant | One verified synthetic workflow. The draft stayed pending approval; this does not prove cloud submission/reply behavior or uptime. |

Raw observations and logs are under `evaluation/`; canonical aggregates are in
`evals/results/`. USD amounts are estimates from returned token usage and recorded
list prices, not invoices. Failed-call usage may be unknown. The historical
architecture benchmark predates later retrieval, approval and fallback fixes;
it should be rerun before making claims about the final implementation.

The eight-page report includes ten actual failed development jobs and preserves
negative results. Its failure table is still narrow: mostly unsupported initial
claims plus a wrong decision, with limited measured repair evidence.

## 4. How Agentic AI course concepts appear in this project

| Course concept | In GigBid | Why it matters |
|---|---|---|
| Agent and tool use | Analyst/risk/writer/critic roles use structured model outputs and bounded MCP capabilities | Model reasoning can request information or draft an action inside a controlled environment. |
| Multi-agent orchestration | Parallel Analyst/Risk/Fit branches, join, conditional edges and two graphs | Different concerns can be analysed independently and combined through explicit state. |
| Typed handoffs | Pydantic JobSpec, RiskReport, FitReport, PriceQuote, ProposalDraft and verdicts | The next node receives validated fields rather than arbitrary prose. |
| RAG and grounding | Search persona evidence, attach source IDs, verify claims before Critic | Generation is supported by retrieved documents; it must not invent work experience. |
| MCP | Portfolio, Marketplace and Workspace expose schemas, resources/prompts and access rules | Agents use a standard capability boundary instead of unrestricted access to databases or services. |
| Reflection | Writer -> Verifier -> Critic -> bounded revision | Drafts can improve from feedback while limits prevent endless loops. |
| Human in the loop | LangGraph interrupt plus edit/approve/reject controls | A recommendation does not become permission to contact a client or spend Connects. |
| Durable execution | Postgres checkpoints, Redis jobs and idempotency | Refreshes/restarts can preserve approvals and avoid duplicate simulator effects. |
| Short- and long-term memory | Current run state versus promoted style/outcome memories | One job's scratch state is different from learning a persistent user preference. |
| Prompt-injection defence | Untrusted job/message boundaries, rules, constrained tools, grounding and approval | Client text cannot grant tool permissions; remaining bypass risks must still be tested. |
| Evaluation and ablation | Retrieval variants, tool granularity, ReAct/supervisor/custom graph comparison | A design earns complexity through measurements; failed hypotheses remain results. |
| Operational agent systems | Scheduling, SSE, traces, token/cost limits, retries and degraded mode | A useful agent system needs recovery, feedback and controls beyond a model call. |

For a viva explanation, use this example: a job asks for a RAG API. Analyst
extracts requirements; Risk checks the client and suspicious instructions; Fit
retrieves relevant portfolio work. The graph decides whether to proceed. Pricing
checks funds, Writer drafts with evidence, Verifier rejects invented experience,
Critic reviews and Compliance checks limits. The UI shows the draft and cost.
Only your approval resumes execution. A later client message enters the separate
conversation workflow and again waits for approval before sending.

## 5. What remains before submission

### First: finish the required public artifacts tonight

1. **Record and upload the three-minute demo.** The timestamped plan is
   `docs/Demo_Script.md`. Show inbox -> analysis -> cited draft -> approval ->
   synthetic client reply, plus scam detection and an injected instruction being
   ignored. Also show Portfolio MCP. A script or screenshot GIF is not a video.
   Keep secrets out of the recording and test the shared video link signed out.
2. **Publish the technical article.** `docs/Technical_Writeup.md` is a prepared
   1,481-word draft, within the required 1,200-1,800 words. Publish it on LinkedIn,
   Medium or a personal blog and add the real URL to README and Classroom.
   The GitHub Markdown file alone is not the specified publication destination.
3. **Provide the human evaluation.** Personally label at least 30 actual drafts
   using the rubric in `evaluation/annotations/README.md`; keep labels independent
   of the judge. Run the judge with the same rubric and retain model/prompt/raw
   outputs/usage. Then compute Cohen's kappa. The CSV currently has blank labels.
   The blind pair packet has 14 pairs; obtain genuine independent ratings and
   keep the randomized architecture key hidden from raters. Never replace human
   labels with generated values or claim these studies are complete.
4. **Complete trace and diagram presentation.** Static saved JSON traces are
   public through GitHub, but three public full tracing views requested by the
   PDF are not established. Phoenix is configured for local/private use. Check
   the instructor accepts sanitized static trace links, or supply approved
   public trace views. Both graphs have code-generated Mermaid source; render
   them visibly for the report/portfolio, rather than only linking `.mmd` files.
5. **Final review, push and submit.** Add the real publication/video links,
   regenerate the report/clean ZIP after any new results, verify the final commit
   and CI, sign in as reviewer from a fresh session and submit before midnight.

The README already has a 30-second animated sequence of actual UI captures.
It is a screenshot slideshow, not a continuous recorded interaction. Replace it
with a short recording-derived GIF if the instructor expects a real walkthrough.
The Portfolio MCP is public/authenticated and has a documented Docker/source
install command plus a tested wheel; PyPI publication is optional under the
assignment's documented-command alternative.

### Required external inputs or verification still missing

- **Instructor GigSim package/API, full persona corpora and development labels.**
  These were not supplied. Obtain them or a clear instructor-approved substitute.
  The local simulator is functional but does not prove hidden-run compatibility.
  Once provided, test the adapter and run the required fixed reply/hire experiment.
- **November 2 policy change request.** Obtain it, implement it, show the actual
  diff, elapsed work and resulting tests. A configurable local surcharge example
  is not evidence that the real change request was completed.
- **Official Upwork and third-party GitHub MCP verification.** Adapter/config
  code exists, but account OAuth, actual tool schemas and allowed live behavior
  have not been demonstrated with the owner's accounts. Use official APIs only.
  Never send real proposals/messages merely to make a demonstration look complete.
- **Hidden test.** It is the instructor's run, not data you should request,
  inspect or tune on. Keep the app accessible and record results only if released.

### Technical and research gaps that can affect marks

- Replay currently supports selected safe bid-drafting stages and a new approval;
  it does not implement the PDF's literal "any job from any node" requirement.
  Conversation replay uses redrafting rather than arbitrary checkpoint replay.
- The named directory structure is mostly present, but some prescribed files are
  consolidated or absent: for example `docs/adr/`, `evals/runners/gigsim_outcomes.py`,
  separate Portfolio `tools.py/resources.py/prompts.py`, Marketplace/Workspace
  per-server test folders and individual API router files. Routes/tools do exist
  elsewhere. Audit exact grader paths; do not add empty files and call it complete.
- Re-run the architecture comparison with balanced quota availability and the
  final code if possible. Current provider-limited results cannot establish the
  required architecture-quality conclusion. Keep the failed original runs.
- Complete a before/after **LLM** injection experiment on both job posts and
  client messages. Current rule-level checks are not that measurement.
- Strengthen independent relevance labels and one-component-at-a-time ablation;
  include proposal utility, persona/job-type breakdowns and real simulator outcomes
  when available. Current component variants are useful but incomplete evidence.
- Broaden the ten-job failure analysis with concrete fixes and measured retests
  across relevant failure categories; do not invent examples to fill categories.
- CI has deterministic 30-job gates. `make eval` currently produces local
  retrieval/rule metrics, not the required official fixed GigSim reply-rate run.
  Prompt-location enforcement and numeric-claim-to-results coverage also need a
  stricter automated gate than the existing source/secret checks.
- The public deployment checks verified a saved pending draft and durable cloud
  storage. A complete hosted approve -> submit -> reply -> response journey,
  evidence-deletion check, idle wake-up and worker restart are still useful final
  acceptance checks. Local E2E/restart success is separate evidence.
- **Free hosting availability:** the Render dashboard warns of inactivity sleep
  and delayed wake-up. Scouting pauses while asleep. Free quotas can interrupt
  inference/storage. An always-available service until grading is not guaranteed.
  Stay within free plans and disclose this; get instructor acceptance or an
  approved free deployment alternative if continuous availability is mandatory.
  Do not use artificial traffic to evade idle policies.

## 6. Exact submission package

Submit together through Google Classroom, following its attachment/link fields:

| Item | Current location/status |
|---|---|
| Public web app | https://gigbid-wr80.onrender.com |
| Public repository | https://github.com/MominMunir/agentic-a2-0854 |
| R&D PDF, at most ten pages | `output/pdf/RnD_Report.pdf` (eight pages currently) |
| Three-minute video URL | Pending recording/upload |
| Portfolio MCP endpoint | https://gigbid-wr80.onrender.com/portfolio/mcp |
| Portfolio installation instructions | Public `mcp_servers/portfolio/README.md` |
| Published technical article URL | Pending external publication |
| Reviewer login | Read local `.private/hosted-reviewer.txt`; share only in a private Classroom comment |
| Source ZIP, if requested | `dist/GigBid_Source.zip`; source and manifests, no runtime secrets/caches |
| Tests/evaluations | `evaluation/`, `evals/results/`, GitHub Actions verification artifact |
| Trace links | Four sanitized static artifacts in `docs/traces/`; public tracing views still to resolve |
| Extension, AI disclosure, resume bullets | `docs/EXTENSION.md`, `docs/AI_USAGE.md`, `docs/Resume_Bullets.md` |

The MCP URL speaks the MCP protocol; it is not a normal webpage. Sign in and mint
a short-lived Portfolio token in Settings for an MCP host. Never put API keys,
database URLs, encryption keys or bearer tokens in Classroom/public source/video.
Only the reviewer account credentials belong in the private reviewer comment.
Keep the live app and backing accounts available until grades are released.

## 7. Prepare for the 15-minute viva

Be ready to demonstrate and locate the relevant code, not only recite terms:

1. Stop Marketplace MCP: show degraded mode, retry/attention state and recovery.
2. Crash around an approved simulator write: show one effect and one debit after
   recovery. Explain the limits of this guarantee for a real upstream service.
3. Hover a claim, open its source, delete the source and regenerate/reverify.
4. Open a wrong-skip trace and identify which decision inputs/node caused it.
5. Show a planted instruction blocked, then explain regex/grounding weaknesses
   and why unknown attacks can still require stronger tests.
6. Make five style observations, explain the repeat threshold, show/delete memory.
7. Explain how the marketplace port changes adapters while graph logic stays the
   same; acknowledge that live OAuth/schema verification is still pending.
8. Explain genuine human/judge disagreements once you have actual labels.
9. Explain why the ReAct run completed more often in the historical study and
   why unequal quotas prevent a causal architecture comparison.
10. Show the real policy-change diff once the instructor request is supplied.

Useful code entry points: `agent/graphs/`, `agent/nodes/`, `agent/handoffs.py`,
`agent/mcp_client.py`, `agent/memory/`, `rag/retriever.py`, `rag/verify.py`,
`mcp_servers/`, `apps/api/main.py`, `worker/` and `evaluation/`.
Read `docs/AI_USAGE.md`: AI assistance was substantial, and you remain
accountable for understanding and changing the submitted system.
