"""Validate the built standalone MCP wheel outside the source tree's imports."""

import asyncio
import json
import os
import subprocess
import sys
import zipfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from gigbid_core.config import ROOT


async def main():
    wheel = next((ROOT / "dist/wheels").glob("*.whl"))
    target = ROOT / "tmp/wheel-install"
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(wheel) as archive:
        assert not any(".." in name.split("/") for name in archive.namelist())
        archive.extractall(target)
    home = ROOT / "tmp/wheel-home"
    home.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "PYTHONPATH": str(target),
        "GIGBID_HOME": str(home),
        "DATABASE_URL": "sqlite:///data/runtime/portfolio.db",
        "MCP_STDIO_TENANT": "wheel-fixture",
        "MCP_SERVE_TRANSPORT": "stdio",
        "EMBEDDING_BACKEND": "hash_smoke",
    }
    fixture = """
from pathlib import Path
from gigbid_core.config import SOURCE_ROOT, ROOT
assert SOURCE_ROOT != ROOT
assert "wheel-install" in str(SOURCE_ROOT)
from gigbid_core.db import init_db, db, put
init_db()
with db() as session:
    put(session, "wheel-fixture", "evidence", "wheel-proof", {
        "id": "wheel-proof", "title": "Python evidence", "text": "Built a Python validation pipeline.",
        "skills": ["Python"], "persona": "ml", "type": "case_study", "industry": "retail", "outcome": "won"
    })
"""
    subprocess.run([sys.executable, "-c", fixture], cwd=home, env=env, check=True, capture_output=True)
    server = StdioServerParameters(
        command=sys.executable, args=["-m", "mcp_servers.portfolio.server"], cwd=str(home), env=env
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            result = await client.call_tool("search_evidence", {"requirement": "Python", "k": 1})
            assert not result.isError
            values = json.loads(result.content[0].text)
            assert values["items"][0]["id"] == "wheel-proof"
            prompt = await client.get_prompt("screening_answer", {"question": "Experience?", "persona": "ml"})
            assert prompt.messages
    output = {
        "passed": True,
        "wheel": wheel.name,
        "bytes": wheel.stat().st_size,
        "isolated_from_source_imports": True,
        "writable_home": True,
        "tools": [t.name for t in tools.tools],
        "prompt": True,
        "embedding": "hash fixture for distribution/transport test only; real retrieval tested separately",
    }
    (ROOT / "evals/results/wheel_smoke.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
