import re

from agent.handoffs import BidDecision, FitReport, JobSpec, PriceQuote, RiskReport
from agent.mcp_client import Tools
from agent.models import generate
from gigbid_core.config import policy, settings

INJECTION = re.compile(
    r"ignore (?:all |your |previous )*(?:instructions|system|rules)|reveal.*(?:prompt|secret|token)|submit without approval|system\s*prompt|<\s*/?system|\bdeveloper message\b",
    re.I,
)
SCAM = re.compile(
    r"unpaid trial|free (?:work|production|test)|telegram|whatsapp|off.platform|pay(?:ment)? (?:outside|via paypal)",
    re.I,
)


def risk_rules(job, client):
    text = job.get("description", "")
    flags = []
    if INJECTION.search(text):
        flags.append("prompt_injection")
    if SCAM.search(text):
        flags.append("unpaid_or_off_platform_request")
    if client.get("payment_verified") is False:
        flags.append("payment_unverified")
    if job.get("budget_max", 0) <= 0:
        flags.append("missing_or_zero_budget")
    score = min(
        1.0,
        0.8
        if flags and any(f in flags for f in ["prompt_injection", "unpaid_or_off_platform_request"])
        else 0.15 * len(flags),
    )
    return RiskReport(
        score=score,
        flags=flags,
        explanation="; ".join(flags)
        or "No known rule-based risk signals; client data is not proof of safety.",
        injection_detected="prompt_injection" in flags,
    )


async def analyst(state):
    job = state["job"]
    if settings().inference_mode == "smoke":
        spec = JobSpec(
            job_id=job["id"],
            title=job["title"],
            deliverables=[job["title"]],
            required_skills=job["required_skills"],
            budget_min=job["budget_min"],
            budget_max=job["budget_max"],
            timeline_days=job["duration_days"],
            screening_questions=job["screening_questions"],
        )
        usage = []
    else:
        spec, use = await generate("analyst", {"job": job}, JobSpec)
        # Extracted facts cannot change the financial or identity source of truth.
        spec.job_id, spec.budget_min, spec.budget_max = job["id"], job["budget_min"], job["budget_max"]
        usage = [use]
    return {"spec": spec.model_dump(), "steps": 1, "usage": usage}


async def risk_assessor(state):
    job = state["job"]
    client = await Tools(state["tenant"], "risk_assessor", state["run_id"]).call(
        "get_client_history", client_id=job["client_id"]
    )
    risk = risk_rules(job, client)
    usage = []
    if settings().inference_mode != "smoke":
        judged, use = await generate("risk_assessor", {"job": job, "client": client}, RiskReport)
        risk.score = max(risk.score, judged.score)
        risk.flags = sorted(set(risk.flags + judged.flags))
        usage = [use]
    return {"risk": risk.model_dump(), "steps": 1, "usage": usage}


async def fit_matcher(state):
    job, profile = state["job"], state["profile"]
    tools = Tools(state["tenant"], "fit_matcher", state["run_id"])
    evidence, matrix = {}, []
    persona = profile.get("persona", "ml")
    whole = None
    if settings().match_query_mode == "whole_job":
        whole = (
            await tools.call(
                "search_evidence", requirement=job["description"], k=10, filters={"persona": persona}
            )
        )["items"]
    for requirement in job["required_skills"]:
        found = (
            {"items": whole}
            if whole is not None
            else await tools.call(
                "search_evidence",
                requirement=requirement + " " + job.get("industry", ""),
                k=5,
                filters={"persona": persona, "type": "case_study"},
            )
        )
        supported = [
            item
            for item in found["items"]
            if requirement.lower() in [s.lower() for s in item["skills"]]
            or requirement.lower() in item["text"].lower()
        ]
        matrix.append({"requirement": requirement, "evidence_ids": [e["id"] for e in supported]})
        evidence.update({item["id"]: item for item in supported})
    matched = [row["requirement"] for row in matrix if row["evidence_ids"]]
    missing = [row["requirement"] for row in matrix if not row["evidence_ids"]]
    fit = FitReport(
        score=len(matched) / max(len(matrix), 1),
        matched_skills=matched,
        missing_skills=missing,
        evidence_ids=list(evidence),
        matrix=matrix,
    )
    return {"fit": fit.model_dump(), "evidence": list(evidence.values()), "steps": 1}


def decision(state):
    limits = policy()
    reasons = []
    exhausted = (
        state.get("steps", 0) >= limits["budgets"]["max_graph_steps"]
        or sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) for u in state.get("usage", []))
        >= limits["budgets"]["max_tokens_per_job"]
    )
    if exhausted:
        return {
            "status": "needs_attention",
            "decision": BidDecision(action="skip", reasons=["Thread budget exhausted"]).model_dump(),
            "steps": 1,
        }
    if state["risk"]["score"] >= limits["thresholds"]["maximum_risk_score"]:
        action, reasons = "skip", state["risk"]["flags"]
    elif state["fit"]["score"] >= limits["thresholds"]["minimum_fit_score"]:
        action, reasons = "bid", ["Portfolio evidence supports sufficient required skills"]
    elif state["fit"]["score"] >= limits["thresholds"]["watch_fit_score"]:
        action, reasons = "watch", ["Partial fit; review missing skills before bidding"]
    else:
        action, reasons = "skip", ["Insufficient portfolio evidence"]
    return {
        "decision": BidDecision(action=action, reasons=reasons).model_dump(),
        "status": "drafting" if action == "bid" else action,
        "steps": 1,
    }


async def pricing(state):
    job, profile = state["job"], state["profile"]
    tools = Tools(state["tenant"], "pricing", state["run_id"])
    wallet = await tools.call("get_connects_balance")
    market = (await tools.call("search_jobs", query=" ".join(job["required_skills"]), limit=200))["jobs"]
    budgets = [
        (j["budget_min"] + j["budget_max"]) / 2
        for j in market
        if not j.get("synthetic", True) and j.get("budget_max", 0) > 0
    ]
    from statistics import median

    anchor = median(budgets) if budgets else (job["budget_min"] + job["budget_max"]) / 2
    floor = profile.get("minimum_project_budget", 200)
    amount = max(floor, min(job["budget_max"], max(job["budget_min"], anchor)))
    connects = job["connects_cost"] + policy()["marketplace"]["connect_surcharge"]
    feasible = (
        amount <= job["budget_max"]
        and connects <= wallet["balance"]
        and wallet["weekly_spent"] + connects <= profile.get("weekly_connects_budget", 100)
    )
    basis = (
        f"Median of {len(budgets)} relevant historical fixed-price postings (USD {anchor:.0f})"
        if budgets
        else "Midpoint of the disclosed project budget; no comparable historical prices available"
    )
    quote = PriceQuote(
        amount=round(amount, 2),
        connects=connects,
        rationale=f"{basis}, clamped to the disclosed USD {job['budget_min']:.0f}-{job['budget_max']:.0f} range and user floor USD {floor}; {connects} Connects. Historical snapshots are advisory, not a causal fair-price estimate.",
        within_budget=feasible,
    )
    return {"price": quote.model_dump(), "status": "drafting" if feasible else "needs_attention", "steps": 1}
