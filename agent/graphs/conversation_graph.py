from langgraph.graph import END, START, StateGraph

from agent.graphs.bid_graph import approval, execute
from agent.handoffs import ProposalDraft
from agent.mcp_client import Tools
from agent.models import generate
from agent.nodes.analysis import INJECTION, SCAM
from agent.nodes.drafting import guard, preview, verifier
from agent.state import BidState
from gigbid_core.config import settings


async def liaison(state):
    tools = Tools(state["tenant"], "client_liaison", state["run_id"])
    messages = (await tools.call("list_messages", conversation_id=state["conversation_id"]))["messages"]
    text = "\n".join(m["text"] for m in messages)
    intent = (
        "scam_signal"
        if INJECTION.search(text) or SCAM.search(text)
        else "interview"
        if any(w in text.lower() for w in ["interview", "availability", "slots"])
        else "negotiation"
        if any(w in text.lower() for w in ["price", "rate", "budget"])
        else "question"
    )
    slots = (await tools.call("free_calendar_slots", days=7))["slots"][:3] if intent == "interview" else []
    if intent == "scam_signal":
        draft = ProposalDraft(
            cover_letter="Please keep communication and payment on this marketplace. I can discuss an agreed paid scope here."
        )
        usage = []
    elif settings().inference_mode == "smoke":
        draft = ProposalDraft(
            cover_letter="I suggest agreeing acceptance criteria and validating each milestone before handover."
            + (
                " Available interview starts (UTC): " + ", ".join(s["start"] for s in slots)
                if slots
                else " What constraint matters most to your team?"
            )
        )
        usage = []
    else:
        draft, use = await generate(
            "client_liaison", {"messages": messages, "slots": slots, "intent": intent}, ProposalDraft
        )
        usage = [use]
    return {
        "messages": messages,
        "intent": intent,
        "slots": slots,
        "draft": draft.model_dump(),
        "evidence": [],
        "usage": usage,
        "steps": 1,
    }


def build_graph(checkpointer, store=None):
    graph = StateGraph(BidState)
    for name, fn in [
        ("client_liaison", liaison),
        ("verifier", verifier),
        ("compliance_guard", guard),
        ("dry_run", preview),
        ("human_review", approval),
        ("execute", execute),
    ]:
        graph.add_node(name, fn)
    graph.add_edge(START, "client_liaison")
    graph.add_edge("client_liaison", "verifier")
    graph.add_edge("verifier", "compliance_guard")
    graph.add_conditional_edges(
        "compliance_guard", lambda s: "dry_run" if s["compliance"]["allowed"] else END
    )
    graph.add_edge("dry_run", "human_review")
    graph.add_conditional_edges("human_review", lambda s: "execute" if s["status"] == "approved" else END)
    graph.add_edge("execute", END)
    return graph.compile(checkpointer=checkpointer, store=store)
