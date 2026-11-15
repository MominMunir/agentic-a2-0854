import json

from gigbid_core.config import ROOT
from scripts.snapshot_tools import schemas


async def test_mcp_signatures_match_snapshot():
    expected = json.loads((ROOT / "tests/contract/tool_schemas.json").read_text(encoding="utf-8"))
    assert await schemas() == expected
