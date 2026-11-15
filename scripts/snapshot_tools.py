import asyncio
import json

from gigbid_core.config import ROOT


async def schemas():
    from importlib import import_module

    output = {}
    for name in ["portfolio", "marketplace", "workspace"]:
        module = import_module("mcp_servers." + name + ".server")
        output[name] = [
            tool.model_dump(mode="json", exclude_none=True) for tool in await module.mcp.list_tools()
        ]
    return output


if __name__ == "__main__":
    output = asyncio.run(schemas())
    path = ROOT / "tests/contract/tool_schemas.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print("MCP schema snapshot saved.")
