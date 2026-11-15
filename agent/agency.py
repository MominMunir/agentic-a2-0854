from agent.mcp_client import Tools
from gigbid_core.config import policy


async def route_team(tenant, job):
    tools = Tools(tenant, "fit_matcher")
    candidates = []
    for persona in ["ml", "web", "data"]:
        evidence = (
            await tools.call(
                "search_evidence",
                requirement=" ".join(job["required_skills"]),
                k=10,
                filters={"persona": persona, "type": "case_study"},
            )
        )["items"]
        proven = {skill for item in evidence for skill in item["skills"]}
        matched = sorted(set(job["required_skills"]) & proven)
        candidates.append(
            {
                "persona": persona,
                "score": len(matched) / max(1, len(job["required_skills"])),
                "matched_skills": matched,
                "evidence_ids": [item["id"] for item in evidence],
            }
        )
    candidates.sort(key=lambda c: c["score"], reverse=True)
    minimum = policy()["thresholds"]["minimum_fit_score"]
    return {
        "selected": candidates[0]["persona"] if candidates[0]["score"] >= minimum else None,
        "candidates": candidates,
        "rule": f"Evidence-supported requirement coverage, minimum {minimum}; ties resolved ml/web/data in that order",
    }
