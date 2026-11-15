# The retriever that lost to its baseline

GigBid began with an appealing assumption: a freelancer copilot should retrieve
better evidence if it combines semantic search, exact keyword matching and a
reranker. The implementation made that possible. The experiment challenged the
assumption. On the project's synthetic development corpus, the dense baseline
won the declared selection rule. Hybrid search and a cross-encoder added
machinery without adding evidence quality. That result changed what the system
ships, and it changed how I think about evaluating agent products.

The product problem is straightforward. A freelancer needs to decide which jobs
deserve attention, show relevant work, propose a sensible price and respond to
clients. A language model can help with the reading and writing. It can also
invent experience, trust a hostile job post or spend Connects on a poor match.
GigBid therefore treats a proposal as an evidence-backed decision artifact.
The important output is a reviewable proposal with its reasons and sources,
followed by a human decision. Fluent text alone is insufficient.

## What the system actually contains

The application uses React and TypeScript for the workspace, FastAPI for the
authenticated API and LangGraph for two durable workflows. The bid graph sends
the same job to an Analyst, Risk Assessor and Fit Matcher in parallel. Their
outputs join before the bid/watch/skip decision. Pricing, writing, verification,
critique and compliance follow. A separate conversation graph handles questions,
negotiation, interview availability and scam signals. Both stop at an approval
interrupt before a marketplace write.

Three MCP servers form the capability boundary. Portfolio provides read-only
evidence search, full case studies, skills, resources and a screening prompt.
Marketplace exposes reads and constrained writes through one internal port.
Workspace supplies calendar slots and approved local draft/hold operations.
The port supports an independent synthetic simulator, an instructor-GigSim REST
adapter and an official-Upwork MCP adapter. Upwork OAuth uses PKCE, state
validation and encrypted per-user tokens. Missing credentials or unverified
tool mappings produce a visible failure instead of a simulated connection.

This distinction matters because the instructor's actual simulator and full
corpora were unavailable. The project does not substitute a local reply for an
instructor outcome. It imports historical jobs from two approved Kaggle sources
and keeps those records separate from generated portfolios, reviews and
conversations. Every record carries provenance. The report's retrieval numbers
come from the frozen synthetic evaluation set, with raw predictions committed
alongside summaries. They do not establish real freelance success.

## Why the baseline won

The comparison holds documents and queries constant across dense retrieval,
requirement decomposition, BM25/dense reciprocal-rank fusion, cross-encoder
reranking, outcome boosting and corrective retrieval. BGE supplies open CPU
embeddings. FlashRank supplies the open reranker. A domain-separated development
split selects the deployed variant; a holdout split measures the selected design
without choosing it again. Exact tables live in `evals/results/retrieval.json`,
and every retrieved ID lives in `evaluation/raw/retrieval.jsonl`.

The corpus has an unusual but revealing structure. A project family appears
across several industries. Case-study prose may be identical while the project
title and industry distinguish the relevant item. Skills and industry metadata
therefore carry substantial information. An early implementation omitted those
headers from indexed text. A live workflow then missed evidence it already had.
Adding the same source headers to every variant fixed the indexing error before
the final comparison. It did not justify adding more retrieval stages.

Fusion can elevate a document because it shares a technical term, even when its
industry is wrong. The reranker in this implementation sees passage text, which
can omit the disambiguating metadata used by the initial retriever. It can then
prefer an otherwise convincing passage from the wrong project family. Outcome
boosting has a related problem: a previously successful proposal from the wrong
context is still the wrong evidence. These are explanations consistent with the
raw rankings, not proof that the methods are generally inferior.

The synthetic task also limits the conclusion. Repeated templates can make
metadata unusually decisive. Real portfolios contain messier descriptions,
implicit skills and inconsistent industry labels. A reranker might help there.
The defensible shipping choice is the measured development winner for the
available corpus, with all variants retained behind configuration. The honest
next experiment uses independent human relevance labels on a messier corpus.

## Grounding is a separate engineering problem

Retrieval does not guarantee truthful proposals. A model can combine a valid
source with an invented percentage or turn a demonstration into years of client
experience. GigBid splits a draft into claims, checks citations and conservatively
requires exact source passages for experience statements. Uncited achievements,
changed metrics and unsupported paraphrases are removed or sent for attention.
Future implementation plans are kept separate from claims about past work.

One practical change made this boundary clearer: experience passages are composed
from evidence bytes rather than generated from memory. The model writes the
surrounding plan and clarification questions. If it fails to include a supported
passage, the composer can include a selected exact source statement with its ID.
The verifier still runs afterward. This reduces the freedom available for past
experience while preserving useful generation for the proposed work.

There is a trade-off. Conservative checking rejects some legitimate paraphrases.
A zero unsupported rate after filtering therefore needs to be read beside how
much text was removed, whether the draft remained useful and whether the source
itself was trustworthy. A synthetic case study can be accurately quoted and still
be inappropriate evidence for a real freelancer. Provenance and human source
review remain essential. The interface makes those boundaries visible instead
of hiding them behind a single confidence score.

## Approval is a transaction boundary

An approval button must do more than toggle a frontend field. GigBid persists a
LangGraph interrupt carrying the draft, supporting evidence, risk, price and
dry-run preview. The authenticated approval endpoint checks the edited text and
creates a capability bound to that user's exact action and content. MCP write
tools reject a mismatched capability. Edits are checked again after the graph
resumes. Refreshing the browser does not lose the pending checkpoint.

The independent simulator commits its wallet debit, proposal and idempotency
ledger together. Replaying an approved effect returns the original result rather
than debiting again. The integration test reopens the disk checkpointer, resumes
the interrupt and calls the same effect twice. Browser tests cover approval,
rejection, edited text, onboarding, mobile layout and a degraded marketplace.
These tests support a precise local recovery claim. They do not prove a remote
provider's behavior during an ambiguous network failure; live reconciliation
and platform confirmation remain separate responsibilities.

## Tool wording and orchestration need evidence too

The tool study compares three surfaces on forty known-call tasks: focused tools,
coarse tools with an operation field and rewritten descriptions. Actual Groq
responses show that clearer-sounding prose does not automatically improve exact
argument names. Selection accuracy and argument accuracy are reported separately.
The tasks are batched, so the token figure is explicitly amortized per task.
Calling that an independently measured per-task cost would overstate the result.

The orchestration runner similarly compares a ReAct agent, a prebuilt supervisor
and the handwritten graph on a fixed development sample. It also compares two
open-model configurations. Provider rate limits, schema/tool failures and
incomplete runs are retained. A supervisor that fails to produce an artifact
cannot be credited with a perfect score merely because its successful subset
looks good. None of those comparisons can supply reply or hire rates without
the missing instructor simulator. Those cells remain unavailable.

The agency extension adds another measurable decision: which persona has proof
for a job's requirements. It queries each persona separately, ranks supported
coverage and refuses a match below the threshold. Its synthetic routing test is
useful for checking evidence isolation. It does not establish that a team would
win more contracts or that skill overlap captures availability and collaboration.

## What I would carry into the next iteration

The main finding is less about a particular embedding model than about the
relationship between data, measurement and authority. Better retrieval machinery
cannot recover metadata it never sees. A successful past proposal is not relevant
merely because it won. A truthful quote is not verified personal experience
merely because it exists in an index. A model recommendation does not authorize
spending money or contacting a client.

The next iteration would obtain the instructor corpus, add independent relevance
and claim labels, calibrate a judge against thirty human assessments and run the
fixed outcome experiment. The current repository includes annotation and
calibration tools, but does not fill human fields with model guesses. Public
deployment and account integration also need their own access checks. Until
those steps happen, the evidence supports a tested local copilot and bounded
research findings. That is a useful result, and a stronger foundation for further
work than an impressive architecture paired with invented success rates.
