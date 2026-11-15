import asyncio

from pydantic import BaseModel

from agent.models import generate
from evaluation.run import save


class Call(BaseModel):
    task_id: int
    tool: str
    arguments: dict


class Batch(BaseModel):
    calls: list[Call]


async def main():
    templates = [
        ("Read the job with ID {id}.", "get_job", "job_id"),
        ("Read the client history for {id}.", "get_client_history", "client_id"),
        ("Find portfolio evidence proving {id}.", "search_evidence", "requirement"),
        ("Read messages in conversation {id}.", "list_messages", "conversation_id"),
        ("Check my remaining Connects balance.", "get_connects_balance", None),
    ]
    tasks = []
    for i in range(40):
        phrase, tool, arg = templates[i % 5]
        value = f"item-{i}" if arg != "requirement" else ["Python", "React", "dbt"][i % 3]
        tasks.append(
            {
                "task_id": i,
                "task": phrase.format(id=value),
                "gold_tool": tool,
                "gold_arguments": {arg: value} if arg else {},
            }
        )
    descriptions = {
        "fine": {
            "get_job": "Get job(job_id).",
            "get_client_history": "Get client(client_id).",
            "search_evidence": "Search evidence(requirement).",
            "list_messages": "List messages(conversation_id).",
            "get_connects_balance": "Read Connects().",
        },
        "coarse": {
            "marketplace_read": "Read marketplace data. arguments: operation (get_job/get_client_history/list_messages/get_connects_balance), plus corresponding job_id/client_id/conversation_id.",
            "portfolio_read": "Read portfolio data. arguments: operation=search_evidence, requirement.",
        },
        "rewritten": {
            "get_job": "Use only to read the full posting for a known job_id; not client history.",
            "get_client_history": "Use only to inspect client hiring/spend history for a client_id; not a job.",
            "search_evidence": "Use only for portfolio proof of a skill or requirement; argument requirement.",
            "list_messages": "Use only to read client messages from a conversation_id; not job posts.",
            "get_connects_balance": "Use only to read remaining Connects; no arguments.",
        },
    }
    rows, summary = [], []
    for variant, tools in descriptions.items():
        result, usage = await generate(
            "router",
            {"tools": tools, "tasks": [{"task_id": t["task_id"], "task": t["task"]} for t in tasks]},
            Batch,
            profile="open_alt",
        )
        by_id = {c.task_id: c for c in result.calls}
        for task in tasks:
            call = by_id.get(task["task_id"])
            expected = task["gold_tool"]
            args = task["gold_arguments"].copy()
            if variant == "coarse":
                args["operation"] = expected
                expected = "portfolio_read" if expected == "search_evidence" else "marketplace_read"
            rows.append(
                {
                    "variant": variant,
                    "task_id": task["task_id"],
                    "gold_tool": expected,
                    "gold_arguments": args,
                    "tool": call.tool if call else None,
                    "arguments": call.arguments if call else None,
                    "selection_correct": bool(call and call.tool == expected),
                    "arguments_correct": bool(
                        call and all(call.arguments.get(k) == v for k, v in args.items())
                    ),
                }
            )
        group = [r for r in rows if r["variant"] == variant]
        summary.append(
            {
                "variant": variant,
                "n": len(group),
                "selection_accuracy": sum(r["selection_correct"] for r in group) / len(group),
                "argument_accuracy": sum(r["arguments_correct"] for r in group) / len(group),
                "amortized_tokens_per_task": (usage["input_tokens"] + usage["output_tokens"]) / 40,
                "usage": usage,
            }
        )
        print("Tool study:", variant, summary[-1]["selection_accuracy"], flush=True)
    save(
        "tool_study",
        rows,
        {
            "design": "40 balanced known-call tasks evaluated in one batch per toolset; tokens/task are amortized, not separately measured task costs",
            "provenance": "synthetic_tools_actual_Groq",
            "results": summary,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
