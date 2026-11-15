from agent.agency import route_team
from agent.mcp_client import Tools


async def test_agency_routes_to_evidence_owner(user):
    for job_id, expected in [("syn-job-001", "ml"), ("syn-job-003", "web"), ("syn-job-007", "data")]:
        job = await Tools(user.id, "scout").call("get_job", job_id=job_id)
        result = await route_team(user.id, job)
        assert result["selected"] == expected
        assert all(e.startswith(expected + "-") for e in result["candidates"][0]["evidence_ids"])
