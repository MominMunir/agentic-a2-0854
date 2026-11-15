from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt

from agent.handoffs import ApprovalRequest
from agent.mcp_client import Tools
from agent.nodes.analysis import analyst, decision, fit_matcher, pricing, risk_assessor
from agent.nodes.drafting import critic, effect_body, guard, preview, verifier, writer
from agent.nodes.drafting import fresh_evidence
from agent.state import BidState
from gigbid_core.config import policy
from gigbid_core.config import settings
from agent.nodes.corrective import corrective_retrieval
from rag.verify import compliance, verify


def fan_out(state):
    return [Send(name, state) for name in ["analyst", "risk_assessor", "fit_matcher"]]


async def approval(state):
    answer = interrupt(
        {
            "draft": state["draft"],
            "evidence": state.get("evidence", []),
            "claims": state.get("verification", {}).get("claims", []),
            "risk": state.get("risk", {}),
            "price": state.get("price", {}),
            "dry_run": state["preview"],
        }
    )
    answer = ApprovalRequest.model_validate(answer)
    if answer.decision == "reject":
        return {"approval": answer.model_dump(), "status": "rejected", "steps": 1}
    text = answer.text or state["draft"]["cover_letter"]
    current = await fresh_evidence(state, state.get("evidence", []))
    checked = verify(text + "\n\n" + "\n\n".join(state["draft"].get("screening_answers", [])), current)
    verdict = compliance(text)
    if checked["unsupported_before"] or not verdict["allowed"]:
        return {
            "approval": answer.model_dump(exclude={"approval_token"}),
            "status": "needs_attention",
            "compliance": {
                "allowed": False,
                "violations": verdict["violations"] + ["Edited text must contain only supported claims."],
            },
            "steps": 1,
        }
    return {
        "approval": answer.model_dump(),
        "evidence": current,
        "draft": {**state["draft"], "cover_letter": text},
        "status": "approved",
        "steps": 1,
    }


async def execute(state):
    tool = "send_message" if state.get("conversation_id") else "submit_proposal"
    result = await Tools(state["tenant"], "approval", state["run_id"]).call(
        tool,
        request={
            **effect_body(state),
            "idempotency_key": state["run_id"],
            "dry_run": False,
            "approval_token": state["approval"]["approval_token"],
        },
    )
    return {"outcome": result, "status": result.get("status", "submitted"), "steps": 1}


def build_graph(checkpointer, store=None):
    graph = StateGraph(BidState)
    graph.add_node("corrective_retrieval", corrective_retrieval)
    graph.add_node("join_analysis", lambda state: {})
    for name, fn in [
        ("analyst", analyst),
        ("risk_assessor", risk_assessor),
        ("fit_matcher", fit_matcher),
        ("decide", decision),
        ("pricing", pricing),
        ("writer", writer),
        ("verifier", verifier),
        ("critic", critic),
        ("compliance_guard", guard),
        ("dry_run", preview),
        ("human_review", approval),
        ("execute", execute),
    ]:
        graph.add_node(name, fn)
    graph.add_conditional_edges(START, fan_out, ["analyst", "risk_assessor", "fit_matcher"])
    graph.add_edge(["analyst", "risk_assessor", "fit_matcher"], "join_analysis")
    graph.add_conditional_edges(
        "join_analysis",
        lambda s: "corrective_retrieval"
        if settings().rag_variant == "v8" and s["fit"]["score"] < 0.55
        else "decide",
    )
    graph.add_edge("corrective_retrieval", "decide")
    graph.add_conditional_edges("decide", lambda s: "pricing" if s["decision"]["action"] == "bid" else END)
    graph.add_conditional_edges("pricing", lambda s: "writer" if s["price"]["within_budget"] else END)
    graph.add_edge("writer", "verifier")
    graph.add_edge("verifier", "critic")
    graph.add_conditional_edges(
        "critic",
        lambda s: "writer"
        if not s["critique"]["accepted"] and s.get("revision", 0) <= policy()["budgets"]["max_revisions"]
        else "compliance_guard",
    )
    graph.add_conditional_edges(
        "compliance_guard", lambda s: "dry_run" if s["compliance"]["allowed"] else END
    )
    graph.add_edge("dry_run", "human_review")
    graph.add_conditional_edges("human_review", lambda s: "execute" if s["status"] == "approved" else END)
    graph.add_edge("execute", END)
    return graph.compile(checkpointer=checkpointer, store=store)
