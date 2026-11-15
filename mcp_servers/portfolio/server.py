from pydantic import Field
from gigbid_core.config import SOURCE_ROOT

from gigbid_core.db import db, records
from gigbid_core.security import tenant
from mcp_servers.common import READ, audit_tool, create_server, serve
from rag.retriever import search

mcp = create_server("GigBid Portfolio", 8101)


@mcp.tool(annotations=READ)
@audit_tool
async def search_evidence(
    requirement: str = Field(min_length=1, max_length=10000),
    k: int = Field(default=5, ge=1, le=20),
    filters: dict | None = None,
) -> dict:
    """Find portfolio proof for a requirement. Filter persona/type/project/industry/outcome; returns exact source text, date and provenance."""
    with db() as session:
        items = records(session, tenant(), "evidence")
    items = [{**item, "_tenant": tenant()} for item in items]
    found = search(items, requirement, k, filters=filters)
    return {"items": [{key: value for key, value in item.items() if key != "_tenant"} for item in found]}


@mcp.tool(annotations=READ)
@audit_tool
async def get_case_study(id: str) -> dict:
    """Load one full evidence item by ID, scoped to the authenticated portfolio owner."""
    with db() as session:
        item = next((i for i in records(session, tenant(), "evidence") if i["id"] == id), None)
    if not item:
        raise ValueError("Evidence not found")
    return item


@mcp.tool(annotations=READ)
@audit_tool
async def list_skills() -> dict:
    """List skills evidenced by this user's portfolio, grouped by persona."""
    with db() as session:
        items = records(session, tenant(), "evidence")
    return {
        "skills": sorted({skill for item in items for skill in item["skills"]}),
        "personas": sorted({item["persona"] for item in items}),
    }


@mcp.resource("portfolio://case/{id}")
async def case_resource(id: str) -> str:
    import json

    return json.dumps(await get_case_study(id))


@mcp.resource("portfolio://proposal/{id}")
async def proposal_resource(id: str) -> str:
    import json

    item = await get_case_study(id)
    if item["type"] != "proposal":
        raise ValueError("Not a proposal evidence item")
    return json.dumps(item)


@mcp.prompt()
def screening_answer(question: str, persona: str) -> str:
    """Answer a screening question using verifiable portfolio proof."""
    return (
        (SOURCE_ROOT / "agent/prompts/portfolio_screening.md")
        .read_text(encoding="utf-8")
        .format(persona=persona, question=question)
    )


def main():
    serve(mcp)


if __name__ == "__main__":
    main()
