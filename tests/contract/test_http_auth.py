from fastapi.testclient import TestClient

from gigbid_core.security import MCPAuth
from mcp_servers.portfolio.server import mcp


def test_http_mcp_requires_bearer_auth():
    with TestClient(MCPAuth(mcp.streamable_http_app())) as client:
        response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        assert response.status_code == 401
