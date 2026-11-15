from mcp.shared.memory import create_connected_server_and_client_session

from gigbid_core.security import tenant_context
from mcp_servers.portfolio.server import mcp


async def test_sdk_resources_prompts_and_search(user):
    marker = tenant_context.set(user.id)
    try:
        async with create_connected_server_and_client_session(mcp._mcp_server) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {"search_evidence", "get_case_study", "list_skills"}
            response = await client.call_tool(
                "search_evidence",
                {"requirement": "Python classification", "k": 3, "filters": {"persona": "ml"}},
            )
            assert not response.isError
            assert len((await client.list_resource_templates()).resourceTemplates) == 2
            assert (await client.list_prompts()).prompts[0].name == "screening_answer"
            resource = await client.read_resource("portfolio://case/ml-project-0-0-case_study")
            assert "classification" in resource.contents[0].text
    finally:
        tenant_context.reset(marker)
