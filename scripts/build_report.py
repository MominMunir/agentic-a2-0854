"""Generate the report and a compact, source-linked PDF from measured artifacts."""

import html
import json
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from gigbid_core.config import ROOT
from scripts.build_docs import load, table


def main():
    deployment = load("public_deployment")
    deployment_note = (
        f"Public deployment verified at {deployment['app_url']}; authenticated Portfolio MCP at "
        f"{deployment['portfolio_mcp_url']}. Reviewer login, an actual open-model draft awaiting approval, "
        "scoped HTTP MCP, Neon checkpoint storage and Qdrant access are recorded in "
        "evals/results/public_deployment.json. This verifies one synthetic workflow, not uptime or hiring outcomes."
        if deployment.get("passed")
        else "Public deployment verification remains an external checkpoint."
    )
    retrieval, tools, decisions, orch, agency = [
        load(n) for n in ["retrieval", "tool_study", "decisions", "orchestration", "agency"]
    ]
    real = json.loads((ROOT / "data/real_manifest.json").read_text())
    synth = json.loads((ROOT / "data/synthetic/manifest.json").read_text())
    raw = ROOT / "evaluation/raw/orchestration.jsonl"
    rows = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()] if raw.exists() else []
    failures = []
    buckets = {kind: [] for kind in ["unsupported draft claim", "wrong bid/skip", "tool/provider error"]}
    for row in rows:
        mismatch = (row.get("decision") == "bid") != (row.get("gold_action") == "bid")
        if not (row.get("error") or mismatch or row.get("unsupported_before", 0)):
            continue
        kind = (
            "tool/provider error"
            if row.get("error")
            else "wrong bid/skip"
            if mismatch
            else "unsupported draft claim"
        )
        buckets[kind].append(row)
    seen = set()
    while len(failures) < 10 and any(buckets.values()):
        for kind, items in buckets.items():
            while items and items[0]["id"] in seen:
                items.pop(0)
            if not items:
                continue
            row = items.pop(0)
            seen.add(row["id"])
            fix = (
                "Verifier removed flagged claims; usefulness unrated."
                if kind == "unsupported draft claim" and row.get("unsupported_after") == 0
                else "Decision repair not evaluated."
                if kind == "wrong bid/skip"
                else "Provider failure retained; rerun incomplete."
            )
            failures.append([row["id"], row["architecture"], kind, fix])
            if len(failures) == 10:
                break
        if not any(buckets.values()):
            break
    rr = [r for r in retrieval.get("results", []) if r["persona"] == "all" and r["split"] == "holdout"]
    rag_rows = [
        [
            r["variant"],
            f"{r['recall_at_5']:.3f}",
            f"{r['mrr']:.3f}",
            f"{r['ndcg_at_10']:.3f}",
            f"{r['p95_seconds']:.3f}",
        ]
        for r in rr
    ]
    tool_rows = [
        [
            r["variant"],
            r["n"],
            f"{r['selection_accuracy']:.3f}",
            f"{r['argument_accuracy']:.3f}",
            f"{r['amortized_tokens_per_task']:.1f}",
        ]
        for r in tools.get("results", [])
    ]
    orch_rows = [
        [
            r["architecture"],
            r["attempted"],
            r["completed"],
            f"{r['decision_accuracy']:.3f}",
            f"{r['unsupported_before_per_draft']:.2f}"
            if r["unsupported_before_per_draft"] is not None
            else "n/a",
            f"{r['p95_seconds']:.1f}",
        ]
        for r in orch.get("results", [])
    ]
    nqueries = len(json.loads((ROOT / "evals/datasets/synthetic_dev.json").read_text()))
    cost_rows = [
        [
            r["architecture"],
            r["drafts"],
            f"{r['mean_tokens']:.0f}" if r["mean_tokens"] is not None else "n/a",
            f"{r['usd_estimate']:.5f}",
            f"{r['analysis_p95_seconds']:.1f}" if r["analysis_p95_seconds"] is not None else "n/a",
            f"{r['proposal_p95_seconds']:.1f}" if r["proposal_p95_seconds"] is not None else "n/a",
        ]
        for r in orch.get("results", [])
    ]
    sections = [
        (
            "1. Problem, constraints and evidence boundaries",
            [
                (
                    "p",
                    "GigBid assists job discovery, risk assessment, fit matching, pricing, proposal writing and client conversations. A freelancer retains authority over every outgoing proposal/message and every Connects debit. The objective is a useful decision workspace with grounded evidence, rather than an unconstrained text generator.",
                ),
                (
                    "p",
                    "Declared budgets, registered before experiments: analysis p95 <=60 s, proposal p95 <=120 s, <=12,000 tokens and <=35 graph steps per thread, at most two Writer revisions, USD 0.05/job and USD 0.10/proposal for inference. USD figures in this report are estimates from actual returned token usage and configured public list prices; they are not the account invoice. Quota delays are included in run latency.",
                ),
                (
                    "p",
                    "The instructor GigSim package, full persona corpus, independent development labels and November 2 policy update were not supplied. I used historical Kaggle jobs, original synthetic portfolios and an independent local simulator. Local simulator responses are demonstration data and are excluded from instructor reply/hire metrics.",
                ),
                (
                    "p",
                    deployment_note,
                ),
                (
                    "p",
                    "Reproducibility: evaluation/raw contains per-query and per-run observations; evals/results contains committed summaries. Source-specific SHA-256 hashes, provenance, software versions and selection rules accompany retrieval results. The report generator reads these files directly. docs/IMPLEMENTATION_PLAN.md records the requirement map and hypotheses before code/experiments.",
                ),
            ],
        ),
        (
            "2. Architecture and R&D A: capability design",
            [
                (
                    "p",
                    "React/TypeScript calls authenticated FastAPI endpoints. Redis/Arq runs scouting and graph work outside web requests. Analyst, Risk Assessor and Fit Matcher run with LangGraph Send and join before decision. Pricing, Writer, claim Verifier, bounded Critic and Compliance follow. A second graph handles conversations. The code-derived diagrams are docs/graphs/bid.mmd and conversation.mmd.",
                ),
                (
                    "p",
                    "Portfolio MCP exposes read-only evidence search, full items, skills, resources and a prompt. Marketplace MCP owns the single port and adapters. Workspace MCP exposes local slots, tentative holds and email drafts. Every write has constrained input, dry run, an idempotency key and a user/action/content-bound approval capability. Per-role tool allowlists constrain access. Official Upwork and GitHub are the only remote service integrations; both require account verification.",
                ),
                (
                    "p",
                    "H-A: focused rewritten tool descriptions improve exact selection over an ambiguous/coarse surface. Forty balanced known-call tasks were evaluated under fine, coarse and rewritten toolsets using actual Groq inference. Each toolset was assessed as one batch, so tokens/task are amortized, not independently timed task costs. Selection and argument accuracy are separate.",
                ),
                ("table", (["Toolset", "n", "Selection", "Arguments", "Tokens/task"], tool_rows)),
                (
                    "p",
                    "Source: evals/results/tool_study.json and evaluation/raw/tool_study.jsonl. Rewritten prose did not improve selection and reduced exact argument accuracy on these tasks. This is a negative result on a small, templated workload; it does not establish a general ranking of tool interfaces. The production surface retains explicit, focused tool schemas and names.",
                ),
            ],
        ),
        (
            "3. Data engineering and RAG methods",
            [
                (
                    "p",
                    f"Two approved Kaggle sources contribute {real['total_jobs']} normalized fixed-price historical jobs. The import scans the original CSV members, validates descriptions, recognizes relevant skills, deduplicates normalized text and retains source row/URL/date/license. Hourly records are not converted into invented fixed budgets. Raw and normalized real text are excluded from release; the manifest, downloader and preprocessing code reproduce it.",
                ),
                (
                    "table",
                    (
                        ["Source", "Metadata license", "Scanned", "Retained"],
                        [
                            [d["dataset"], d["license"], d["rows_scanned"], d["kept"]]
                            for d in real["datasets"]
                        ],
                    ),
                ),
                (
                    "p",
                    f"Original seed-4016 synthetic data contains {synth['counts']['evidence']} evidence items, {synth['counts']['jobs']} jobs, plus tagged clients, reviews, proposal histories and conversations. All evidence carries persona/type/project/skills/date/industry/outcome/source/provenance. Real, synthetic and user-upload records have distinct tags and file locations. Full rationale, licensing caveats and limitations are in docs/DATA_CARD.md.",
                ),
                (
                    "p",
                    "PDF/text/Markdown/JSON/code ingestion uses stable content-hash chunks and incremental updates. GitHub file ingestion uses official read-only MCP. BGE-small supplies open CPU dense embeddings; FlashRank MiniLM is the open cross-encoder. Qdrant serves production vectors, and NumPy cosine is the local reference backend. All evaluated variants share identical document headers with title, skills and industry.",
                ),
                (
                    "p",
                    "Implemented variants: V0 fixed-document dense cosine; V1 requirement/query decomposition and merge; V2 BM25+dense reciprocal rank fusion; V3 cross-encoder over hybrid candidates; V4 outcome boost; V8 bounded corrective retrieval, with a graph-level re-query/refusal path. H-B predicted improved evidence recall from decomposition/fusion. The split is by industry: four development domains and two holdout domains. Template-generated relevance is not an independent human gold set.",
                ),
            ],
        ),
        (
            "4. R&D B: retrieval and grounding results",
            [
                ("table", (["Variant", "Recall@5", "MRR", "nDCG@10", "p95 s"], rag_rows)),
                (
                    "p",
                    f"Source: evals/results/retrieval.json; {nqueries} frozen synthetic queries across three personas and six variants. Selection uses development Recall@5, then nDCG@10, then lower p95; the holdout never selects the winner. The rule chose {retrieval.get('selected_variant')}, which is the deployed default. Per-persona results and job types remain in the raw files.",
                ),
                ("image", "evaluation/retrieval_comparison.png"),
                (
                    "p",
                    "The advanced stages failed to improve this corpus. Shared project prose makes industry metadata unusually decisive. RRF can elevate exact technical matches from the wrong industry; the current reranker sees passage text without all initial metadata. Outcome boosts can prefer a successful but contextually wrong item. These are plausible failure mechanisms visible in rankings, not proof of general inferiority. V1/V2/V3/V4/V8 provide component-removal comparisons; a factorial independently labeled ablation remains future work.",
                ),
                (
                    "p",
                    "After drafting, sentences are split and classified supported/partly-supported/unsupported. Experience needs an exact cited source passage; altered numbers, invented tenure and unknown citations fail. Unsupported text is removed before Critic, with counts retained. Five adversarial claim challenges are recorded in evals/results/claim_challenge.json. A zero post-filter unsupported rate must be read beside removed content and usefulness; this conservative verifier is not a semantic entailment oracle.",
                ),
                (
                    "p",
                    "Independent human proposal ratings, a 30-item human/judge calibration and instructor reply/hire rates are unavailable. evaluation/human_panel.py prepares blinded packets, computes Cohen kappa only after at least 30 supplied paired labels, and calculates pairwise statistics. It never fills human columns with model guesses. A calibrated judge score is therefore not claimed.",
                ),
            ],
        ),
        (
            "5. R&D C: orchestration and model profiles",
            [
                (
                    "p",
                    "H-C predicts that isolated roles reduce unsupported claims/compliance failures relative to one ReAct agent, with extra latency and tokens. The runner compares an actual prebuilt ReAct agent, langgraph-supervisor and the handwritten graph on the same development jobs. A second handwritten profile uses gpt-oss-20b for both tiers; the primary profile uses 20b for cheap nodes and 120b for writing/critique. Tool responses, prompts, no-write constraints and common post-verification are explicit.",
                ),
                ("table", (["Architecture", "Tried", "Done", "Accuracy*", "Raw claims", "p95 s"], orch_rows)),
                (
                    "p",
                    f"Source: evals/results/orchestration.json and evaluation/raw/orchestration.jsonl. Requested jobs per architecture: {orch.get('n_per_architecture', 'pending')}. Failed attempts are retained. Accuracy denominator is documented in the source summary; completion rate must be assessed alongside accuracy on successful runs. Tokens and cost are actual returned usage for completed calls. Provider errors may omit partial usage, so failed-call cost is unknown rather than zero.",
                ),
                (
                    "p",
                    "Groq daily quotas caused 49/50 supervisor failures and most graph failures. Sequential groups had unequal token availability, so this operational study cannot fairly rank architectures or confirm H-C. The table p95 includes all attempts, including fast rejections; completed/proposal p95 are separate JSON fields. n/a means no drafts, not zero unsupported claims. Models are open-weight; CPU retrieval remains local and open.",
                ),
                (
                    "table",
                    (
                        [
                            "Architecture",
                            "Drafts",
                            "Mean tokens / done",
                            "USD total*",
                            "Analysis p95 s",
                            "Draft p95 s",
                        ],
                        cost_rows,
                    ),
                ),
                (
                    "p",
                    "*USD totals cover returned usage on completed jobs only; failed-call usage is unknown. Baseline prices were derived from preserved token counts and recorded model IDs. Analysis time is measured through decision, and draft latency through the approval/terminal state. Network/retry latency is included; these are client observations, not server decoding tokens/second. Budget enforcement blocks writes after returned usage exceeds limits; a request may cross a budget before its usage is known.",
                ),
                (
                    "p",
                    "No instructor GigSim service means no simulated reply/hire comparison can be completed, and no hidden test has been run. The local simulator deliberately generates a sample reply for UI exercises; counting it as a research reply rate would be invalid. The production decision is justified by tested control boundaries and available evidence, with generalization and outcome claims left open.",
                ),
            ],
        ),
        (
            "6. Reliability, security and production engineering",
            [
                (
                    "p",
                    "State, execution trace and long-term memory use distinct stores. Postgres checkpoints preserve interrupts. Event/audit rows record redacted observations. A durable LangGraph BaseStore separates tenant-specific style/outcome namespaces. Style promotion requires five edit observations with a deletion repeated in at least three; outcome aggregation requires three distinct confirmed jobs. Settings exposes deletion. Raw tool output is never promoted directly.",
                ),
                (
                    "p",
                    "The approval endpoint rechecks edited text, mints an expiring content-bound capability and queues graph resumption. The graph rechecks again. The local simulator atomically commits its effect ledger, wallet debit and proposal/message. Duplicate calls with the same content return the original result; changed content under the same key fails. Unit/integration tests reopen the on-disk checkpointer and verify one debit after retry. External exactly-once effects require an upstream idempotency contract and reconciliation after ambiguous failures.",
                ),
                (
                    "p",
                    "Job posts/messages are delimited untrusted data. Deterministic injection/off-platform/free-work rules supplement model risk. Agents cannot mint approval tokens. PII is masked in logs; OAuth tokens are encrypted and scoped by user. The HTTP MCP endpoint requires tenant bearer authentication. API sessions use HttpOnly/SameSite cookies, origin checks, constrained uploads and tenant ownership checks. Local rate-limit and outage handling are explicit. Rule-level injection routing is measured; a broad model attack-success claim is not made.",
                ),
                (
                    "p",
                    "CI includes tests, schema snapshots, secret/instructor-directory gates and a 30-job deterministic smoke eval. Playwright verifies six browser journeys. Compose runs the full stack with independent workers. The free Render profile shares the API process with a Redis/Arq background worker, using external Neon/Qdrant storage. An initial cloud OOM after warmed retrieval plus sign-in prompted this change; a 512 MiB regression check now repeats sign-in three times and measured 432.22 MiB peak. Hashing parameters and model weights were retained. Free sleep prevents an always-live guarantee; docs/FREE_DEPLOYMENT.md records limits.",
                ),
                (
                    "p",
                    "Dependency audits were run after upgrading affected libraries. The supported MCP 1.x line is retained because the required LangChain adapter caps SDK <2; its tested release has no remaining reported advisory in the recorded audit. The current lockfile fixes transitive versions. The audit is a point-in-time check, not a guarantee that software is vulnerability-free.",
                ),
                (
                    "p",
                    "A separate registration failure required 999 database operations during account setup. Batched seeding reduced the local count to two, and a fresh public account registered in 2.26 seconds while health checks continued responding. The check verified the initial wallet, portfolio, messages, login and tenant isolation without sending proposals. Sources: evals/results/registration.json and registration_local.json.",
                ),
            ],
        ),
        (
            "7. Extension, policy change and failure analysis",
            [
                (
                    "p",
                    f"X1 agency routing compares evidence-supported requirement coverage across personas, selects only above threshold and drafts using the chosen member. Its frozen synthetic routing evaluation reports n={agency.get('n', 'pending')}, accuracy={agency.get('accuracy', 'pending')}; source evals/results/agency.json. This measures routing correctness and evidence isolation, not hiring success or team availability.",
                ),
                (
                    "p",
                    "The November 2 policy change was not supplied, so its implementation effort could not be evaluated. Connects surcharge, polling intervals, thresholds and budgets are configuration values. A local surcharge test demonstrates cost recalculation; it does not evaluate the missing instructor change request.",
                ),
                ("table", (["Dev job", "Design", "Failure category", "Fix status"], failures)),
                (
                    "p",
                    "The table selects ten unique development jobs across unsupported claims, wrong decisions and provider failures. The verifier removed the flagged claims in the cited cases; human usefulness ratings are still required. Separate integration failures included omitted metadata, checkpoint-driver incompatibility and a signup redirect race. Their regression checks passed. Independent development labels are needed to extend the taxonomy to pricing and proposal-quality failures.",
                ),
            ],
        ),
        (
            "8. Conclusions, reproducibility and remaining gates",
            [
                (
                    "p",
                    "The available evidence supports a functioning freelancer workspace with evidence retrieval, typed parallel analysis, bounded critique, durable human approval, exactly-once simulator effects and measurable agency routing. It does not establish real freelance earnings, causal reply improvements, unseen hidden-test quality or verified live Upwork behavior. "
                    + deployment_note,
                ),
                (
                    "p",
                    "Reproduce with uv sync --frozen --extra dev --extra retrieval; bootstrap, generate_data and seed; then pytest, evaluation.run, evaluation.tool_study, evaluation.orchestration --limit 50 and evaluation.agency_eval. Frontend npm ci/build/test:e2e uses a generated OpenAPI contract. Raw metrics, plots, tests and logs are retained in evaluation; summaries are in evals/results. docs/RUNBOOK.md covers deployment, recovery and GitHub publication.",
                ),
                (
                    "p",
                    "Human proposal ratings, judge calibration and a blind panel were not conducted. Instructor simulator outcomes and the policy-change study require the missing materials. Live Upwork/GitHub account integration remains unverified; hidden evaluation is performed by the instructor. The technical article is published at https://gigbid-wr80.onrender.com/blog/gigbid. Reviewer access is shared privately; the demo video is submitted separately.",
                ),
                (
                    "p",
                    "Primary references: LangGraph persistence and interrupts (docs.langchain.com/oss/python/langgraph); official MCP Python SDK (github.com/modelcontextprotocol/python-sdk); official GitHub MCP (github.com/github/github-mcp-server); official Upwork MCP (upwork.com/ai/mcp); Groq supported models/pricing (console.groq.com/docs/models); Phoenix deployment/authentication (arize.com/docs/phoenix/deployment/authentication). Dataset attribution and terms are preserved in docs/DATA_CARD.md and data/real_manifest.json.",
                ),
                (
                    "p",
                    "Design conclusion: retain the measured retrieval winner and hard approval/grounding boundaries. Advanced retrieval and more agents should earn their complexity on independent data. Preserve negative results, failed attempts and missing measurements; they are operational evidence for the next iteration.",
                ),
            ],
        ),
    ]
    sections += [
        ("9. Compiled bid workflow", [("graph", ("docs/graphs/bid.png", 6.55, 8.65))]),
        ("10. Compiled conversation workflow", [("graph", ("docs/graphs/conversation.png", 5.8, 7.2))]),
    ]
    markdown = ["# GigBid R&D report", "Muhammad Momin Munir | 22I-0854 | Agentic AI Assignment-02", ""]
    for title, blocks in sections:
        markdown += ["## " + title, ""]
        for kind, value in blocks:
            if kind == "p":
                markdown += [value, ""]
            elif kind == "table":
                markdown += [table(value[0], value[1]), ""]
            elif kind == "image":
                markdown += [f"![Retrieval comparison](../{value})", ""]
            elif kind == "graph":
                markdown += [f"![{title}](../{value[0]})", ""]
    (ROOT / "docs/RnD_Report.md").write_text("\n".join(markdown), encoding="utf-8")
    output = ROOT / "output/pdf/RnD_Report.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="AssignmentTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=23,
            spaceAfter=10,
            textColor=colors.HexColor("#195d4b"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="StudentDetails",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            spaceAfter=4,
            textColor=colors.HexColor("#253b38"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="GigCaption",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#84937f"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="GigBody",
            fontName="Helvetica",
            fontSize=9.3,
            leading=13.2,
            spaceAfter=11,
            textColor=colors.HexColor("#34413d"),
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="GigHeading",
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=24,
            spaceAfter=19,
            textColor=colors.HexColor("#195d4b"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="GigCell",
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#34413d"),
        )
    )
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=50,
        bottomMargin=42,
        title="GigBid R&D report",
        author="Muhammad Momin Munir",
    )
    story = []
    for index, (title, blocks) in enumerate(sections):
        if index:
            story.append(PageBreak())
        else:
            story.append(Paragraph("Agentic AI Assignment-02", styles["AssignmentTitle"]))
            story.append(
                Paragraph("<b>Name:</b> Muhammad Momin Munir", styles["StudentDetails"])
            )
            story.append(Paragraph("<b>Roll Number:</b> 22I-0854", styles["StudentDetails"]))
            story.append(Spacer(1, 20))
        story.append(Paragraph("GIGBID / ENGINEERING REVIEW", styles["GigCaption"]))
        story.append(Spacer(1, 9))
        story.append(Paragraph(html.escape(title), styles["GigHeading"]))
        for kind, value in blocks:
            if kind == "p":
                value = re.sub("[\u2010-\u2015]", "-", value)
                story.append(Paragraph(html.escape(value), styles["GigBody"]))
            elif kind == "table":
                headers, data = value
                if not data:
                    story.append(
                        Paragraph("External measurement pending; no values fabricated.", styles["GigBody"])
                    )
                    continue
                cells = [
                    [Paragraph(html.escape(str(x)), styles["GigCell"]) for x in row]
                    for row in [headers] + data
                ]
                widths = [(A4[0] - 84) / len(headers)] * len(headers)
                tab = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
                tab.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f0e4")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dae1d6")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 7),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ]
                    )
                )
                story += [tab, Spacer(1, 13)]
            elif kind == "image":
                story += [Image(str(ROOT / value), width=6.6 * inch, height=2.44 * inch), Spacer(1, 10)]
            elif kind == "graph":
                path, width, height = value
                story.append(Image(str(ROOT / path), width=width * inch, height=height * inch))

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#7f8d80"))
        canvas.drawString(42, 23, "GigBid | AI-4016 Assignment 02")
        canvas.drawRightString(A4[0] - 42, 23, str(document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    from pypdf import PdfReader

    pages = len(PdfReader(output).pages)
    if pages > 10:
        raise RuntimeError(f"Report exceeds the assignment page limit: {pages}")
    print(f"Report exported and page count checked: {pages} pages.")


if __name__ == "__main__":
    main()
