from agent.handoffs import ComplianceVerdict, Critique, ProposalDraft
from agent.mcp_client import Tools
from agent.models import generate
from gigbid_core.config import policy, settings
from rag.verify import compliance, verify


async def fresh_evidence(state, items):
    current = []
    tools = Tools(state["tenant"], "writer", state["run_id"])
    for item in items:
        try:
            current.append(await tools.call("get_case_study", id=item["id"]))
        except Exception as exc:

            def missing(error):
                nested = getattr(error, "exceptions", None)
                return all(missing(item) for item in nested) if nested else "not found" in str(error).lower()

            if not missing(exc):
                raise
    return current


async def writer(state):
    current = await fresh_evidence(state, state["evidence"])
    evidence = sorted(
        current,
        key=lambda e: (e["type"] != "case_study", e.get("industry") != state["job"].get("industry")),
    )[:5]
    if settings().inference_mode == "smoke":
        passages = "\n\n".join(f"{e['text']} [{e['id']}]" for e in evidence[:2])
        text = f"Your {state['job']['title']} needs reproducible deliverables and clear validation.\n\n{passages}\n\nI propose a short discovery step, an implementation milestone and a documented validation handover. Which deliverable should we prioritize first?"
        draft = ProposalDraft(
            cover_letter=text,
            evidence_ids=[e["id"] for e in evidence[:2]],
            screening_answers=[
                "I would agree acceptance criteria first, use a held-out validation set where appropriate, and document limitations."
            ],
        )
        usage = []
    else:
        from agent.memory.store import read_memory

        draft, use = await generate(
            "writer",
            {
                "job": state["spec"],
                "profile": state["profile"],
                "voice": policy()
                .get("agency", {})
                .get("voices", {})
                .get(state["profile"].get("persona"), ""),
                "price": state["price"],
                "evidence": evidence,
                "style_memory": read_memory(state["tenant"], "style"),
                "feedback": state.get("critique"),
                "revision": state.get("revision", 0),
            },
            ProposalDraft,
        )
        usage = [use]
        # Evidence passages are composed from source bytes, never generated facts.
        checked = verify(draft.cover_letter, evidence)
        if evidence and not any(c["status"] == "supported" and c["evidence_ids"] for c in checked["claims"]):
            source = evidence[0]
            draft.cover_letter += "\n\n" + source["text"] + " [" + source["id"] + "]"
            draft.evidence_ids = sorted(set(draft.evidence_ids + [source["id"]]))
    index = state.get("regenerate_index")
    if index is not None and state.get("draft"):
        paragraphs = state["draft"]["cover_letter"].split("\n\n")
        generated = draft.cover_letter.split("\n\n")
        if 0 <= index < len(paragraphs):
            paragraphs[index] = generated[min(index, len(generated) - 1)]
            draft.cover_letter = "\n\n".join(paragraphs)
    return {
        "draft": draft.model_dump(),
        "evidence": current,
        "regenerate_index": None,
        "steps": 1,
        "usage": usage,
    }


def verifier(state):
    result = verify(state["draft"]["cover_letter"], state["evidence"])
    answers = [verify(answer, state["evidence"]) for answer in state["draft"].get("screening_answers", [])]
    draft = {
        **state["draft"],
        "cover_letter": result["text"],
        "screening_answers": [a["text"] for a in answers],
    }
    result["screening_claims"] = [c for a in answers for c in a["claims"]]
    return {"verification": result, "draft": draft, "steps": 1}


async def critic(state):
    text = state["draft"]["cover_letter"]
    issues = []
    if len(text.split()) < 35:
        issues.append("Insufficient substantive content after verification")
    if not any(c["evidence_ids"] and c["status"] == "supported" for c in state["verification"]["claims"]):
        issues.append("Include a supported exact evidence passage")
    usage = []
    if settings().inference_mode != "smoke":
        critique, use = await generate(
            "critic",
            {"draft": state["draft"], "job": state["spec"], "verification": state["verification"]},
            Critique,
        )
        issues += critique.reasons if not critique.accepted else []
        usage = [use]
    critique = Critique(accepted=not issues, reasons=issues)
    return {
        "critique": critique.model_dump(),
        "revision": state.get("revision", 0) + (1 if issues else 0),
        "usage": usage,
        "steps": 1,
    }


def guard(state):
    verdict = compliance(
        state["draft"]["cover_letter"] + "\n" + "\n".join(state["draft"].get("screening_answers", []))
    )
    if not state.get("critique", {}).get("accepted", True):
        verdict["violations"].append("Critic did not accept the draft within the revision limit.")
    if not state.get("price", {}).get("within_budget", True):
        verdict["violations"].append("Price or Connects exceed the configured budget.")
    budget = policy()["budgets"]
    if (
        state.get("steps", 0) >= budget["max_graph_steps"]
        or sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) for u in state.get("usage", []))
        >= budget["max_tokens_per_job"]
        or sum(u.get("usd_estimate", 0) for u in state.get("usage", [])) > budget["max_usd_per_job"]
    ):
        verdict["violations"].append("Thread step, token or cost budget exceeded.")
    verdict["allowed"] = not verdict["violations"]
    return {
        "compliance": ComplianceVerdict(**verdict).model_dump(),
        "status": "awaiting_approval" if verdict["allowed"] else "needs_attention",
        "steps": 1,
    }


async def preview(state):
    tool = "send_message" if state.get("conversation_id") else "submit_proposal"
    body = effect_body(state)
    result = await Tools(state["tenant"], "approval", state["run_id"]).call(
        tool, request={**body, "idempotency_key": state["run_id"], "dry_run": True}
    )
    return {"preview": result, "steps": 1}


def effect_body(state, text=None):
    if state.get("conversation_id"):
        return {"conversation_id": state["conversation_id"], "text": text or state["draft"]["cover_letter"]}
    return {
        "job_id": state["job"]["id"],
        "text": text or state["draft"]["cover_letter"],
        "bid": state["price"]["amount"],
        "expected_connects_cost": state.get("preview", {}).get("connects_cost", state["price"]["connects"]),
        "screening_answers": state["draft"].get("screening_answers", []),
    }
