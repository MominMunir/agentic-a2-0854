import json

from gigbid_core.config import ROOT


def load(name):
    path = ROOT / "evals/results" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        + ["| " + " | ".join(str(x) for x in row) + " |" for row in rows]
    )


def main():
    deployment = load("public_deployment")
    live_links = (
        f"**Live app:** [{deployment['app_url']}]({deployment['app_url']}) · "
        f"[Portfolio MCP]({deployment['portfolio_mcp_url']}) (authenticated MCP endpoint).\n\n"
        "Verified reviewer login, real-model drafting, scoped MCP and durable cloud storage: "
        "[deployment checks](evals/results/public_deployment.json)."
        if deployment.get("passed")
        else "Public deployment verification is in progress."
    )
    retrieval, tools, decisions, orchestration, agency = [
        load(n) for n in ["retrieval", "tool_study", "decisions", "orchestration", "agency"]
    ]
    rr = [r for r in retrieval.get("results", []) if r["split"] == "holdout" and r["persona"] == "all"]
    rag_table = table(
        ["Variant", "Recall@5", "MRR", "nDCG@10", "Retrieval p95 (s)"],
        [
            [
                r["variant"],
                f"{r['recall_at_5']:.3f}",
                f"{r['mrr']:.3f}",
                f"{r['ndcg_at_10']:.3f}",
                f"{r['p95_seconds']:.3f}",
            ]
            for r in rr
        ],
    )
    tool_table = table(
        ["Toolset", "Tasks", "Selection accuracy", "Argument accuracy", "Amortized tokens/task"],
        [
            [
                r["variant"],
                r["n"],
                f"{r['selection_accuracy']:.3f}",
                f"{r['argument_accuracy']:.3f}",
                f"{r['amortized_tokens_per_task']:.1f}",
            ]
            for r in tools.get("results", [])
        ],
    )
    orch_table = table(
        [
            "Architecture",
            "Attempted",
            "Completed",
            "Decision accuracy*",
            "Unsupported before/draft",
            "p95 (s)",
        ],
        [
            [
                r["architecture"],
                r["attempted"],
                r["completed"],
                f"{r['decision_accuracy']:.3f}",
                f"{r['unsupported_before_per_draft']:.3f}"
                if r["unsupported_before_per_draft"] is not None
                else "n/a (no drafts)",
                f"{r['p95_seconds']:.2f}",
            ]
            for r in orchestration.get("results", [])
        ],
    )
    (ROOT / "docs/RESULTS.md").write_text(
        "# Reproducible measurements\n\n"
        + rag_table
        + "\n\nSource: `evals/results/retrieval.json`; synthetic domain holdout, actual open CPU models.\n\n"
        + tool_table
        + "\n\nSource: `evals/results/tool_study.json`; actual Groq inference, batched synthetic tasks.\n\n"
        + orch_table
        + "\n\nSource: `evals/results/orchestration.json`. *Accuracy denominator is specified in the source summary. Failed attempts remain visible. Reply/hire rates unavailable without instructor GigSim.\n",
        encoding="utf-8",
    )
    (ROOT / "docs/graphs").mkdir(exist_ok=True)
    from langgraph.checkpoint.memory import InMemorySaver
    from agent.graphs.bid_graph import build_graph as bid
    from agent.graphs.conversation_graph import build_graph as conversation

    for name, fn in [("bid", bid), ("conversation", conversation)]:
        (ROOT / f"docs/graphs/{name}.mmd").write_text(
            fn(InMemorySaver()).get_graph().draw_mermaid(), encoding="utf-8"
        )
    schema = json.loads((ROOT / "tests/contract/tool_schemas.json").read_text(encoding="utf-8"))
    inventory = []
    for server, entries in schema.items():
        for item in entries:
            annotation = item.get("annotations", {})
            inventory.append(
                [
                    item["name"],
                    server,
                    "read" if annotation.get("readOnlyHint") else "write",
                    " / ".join(f"{k}={v}" for k, v in annotation.items() if k.endswith("Hint")),
                    "tenant bearer / scoped stdio",
                ]
            )
    (ROOT / "docs/TOOLS.md").write_text(
        "# MCP tool inventory\n\n"
        + table(["Tool", "Owner/server", "Access", "Annotations", "Authentication"], inventory)
        + "\n\nSchemas and descriptions: `tests/contract/tool_schemas.json`. Every write accepts an idempotency key and dry-run preview; non-preview effects require an exact content-bound approval capability. Audit rows redact PII and exclude capability tokens.\n\n## Third-party trust\n\n- [Official Upwork MCP](https://www.upwork.com/ai/mcp): operated by the marketplace; OAuth scopes and explicit draft-only mapping constrain authority. Account validation is pending.\n- [Official GitHub MCP](https://github.com/github/github-mcp-server): operated by GitHub; used only for read-only repository files, with code treated as data.\n\nOnly per-role named tools are exposed to graph code. Client timeouts and retries are bounded. Missing endpoints produce saved retry/attention states.\n",
        encoding="utf-8",
    )
    readme = f"""# GigBid

![Actual UI walkthrough with synthetic demonstration data](docs/images/demo.gif)

**Find worthwhile freelance work. Write proposals with proof. Approve every action.**

GigBid combines a React workspace, durable LangGraph workflows and three MCP
servers. Requirement-to-evidence matching, risk assessment, grounded drafting,
pricing and client replies stay visible and reviewable.

Source: [MominMunir/agentic-a2-0854](https://github.com/MominMunir/agentic-a2-0854).

{live_links}

![Inbox](docs/images/inbox-desktop.png)

## Run locally

```sh
git clone https://github.com/MominMunir/agentic-a2-0854.git
cd agentic-a2-0854
uv sync --frozen --extra dev --extra retrieval
uv run python scripts/bootstrap.py
uv run python scripts/generate_data.py
# Set OPEN_MODEL_API_KEY privately in .env (Groq open models), or select Ollama.
uv run python scripts/seed.py
docker compose up --build -d
```

Open http://localhost:8080. This is a local address, not a public deployment.
The full [runbook](docs/RUNBOOK.md) covers Windows development, local Ollama,
deployment, GitHub publication, recovery and secret handling.

## Architecture

```mermaid
flowchart LR
  UI[React workspace] --> API[FastAPI]
  API --> W[Redis / Arq]
  W --> G[LangGraph parallel analysis]
  G --> P[Portfolio MCP / open retrieval]
  G --> M[Marketplace MCP / one port]
  G --> C[Workspace MCP]
  G --> H[Human interrupt]
  H --> UI
  G --> DB[Postgres checkpoints and memory]
  G --> T[OpenTelemetry / Phoenix]
```

See [architecture](docs/ARCHITECTURE.md), [tool contracts](docs/TOOLS.md),
[data provenance](docs/DATA_CARD.md), and [code-generated graph diagrams](docs/graphs).
The independent local simulator is explicitly separate from the missing
instructor GigSim. Live Upwork uses official MCP/OAuth and requires account/tool
mapping verification. No scraping or automatic platform confirmation is used.

## Retrieval results

{rag_table}

Source: `evals/results/retrieval.json`, synthetic domain holdout. The development
selection rule chose **{retrieval.get("selected_variant", "pending")}**. No human-panel or instructor outcome claim follows from these scores.

## Orchestration results

{orch_table}

Source: `evals/results/orchestration.json`; actual Groq calls on synthetic jobs.
Read its sample size, completion counts and accuracy denominator before comparing
systems. Sequential groups encountered unequal daily token availability: 49 of 50
supervisor attempts were rejected by the quota. This cannot fairly rank architectures.
The p95 column includes failed attempts. No-draft claim rates are unavailable.
Provider failures are retained. Reply/hire rates require the unavailable
instructor simulator and are not invented. Actual USD figures are usage-based
public-price estimates, not an account invoice.

## Verify and reproduce

```sh
uv run python -m pytest -q
uv run python -m evaluation.run
uv run python -m evaluation.tool_study
uv run python -m evaluation.orchestration --limit 50
uv run python -m evaluation.agency_eval
cd apps/web
npm ci
npm run test:e2e
```

Raw metrics and logs: `evaluation/`. Summaries: `evals/results/`.
Current browser tests exercise onboarding/upload, approval, rejection, editing,
degraded mode and mobile layout. Model/API studies can be subject to quota limits.

## Deliverables and publication status

- [R&D report](docs/RnD_Report.md) and [PDF](output/pdf/RnD_Report.pdf)
- [Technical article](docs/Technical_Writeup.md), [three-minute script](docs/Demo_Script.md)
- [Standalone Portfolio MCP](mcp_servers/portfolio/README.md)
- [X1 agency extension](docs/EXTENSION.md) and [AI disclosure](docs/AI_USAGE.md)
- [Requirement ledger](docs/IMPLEMENTATION_PLAN.md)
- [Free Render deployment](docs/FREE_DEPLOYMENT.md) and [GitHub steps](docs/RUNBOOK.md#public-github-repository-steps-required-by-the-pdf)
- [Verified public deployment status](docs/DEPLOYMENT_STATUS.md)
- [Three saved workflow traces](docs/traces/README.md) and [resume bullets](docs/Resume_Bullets.md)

The source repository is public. See the live deployment status above and the
free deployment guide. Article/video publication remains pending. Reviewer
credentials are generated from environment variables, excluded from the release,
and shared privately. The owner confirmed an extension to midnight PKT at the end
of November 15, 2026; the original PDF lists November 12. Commit dates remain
unaltered. See [the submission and viva guide](docs/SUBMISSION_GUIDE.md).
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("README, results tables, tool inventory and code-derived graph diagrams regenerated.")


if __name__ == "__main__":
    main()
