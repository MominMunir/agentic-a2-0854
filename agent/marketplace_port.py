from typing import Protocol


class MarketplacePort(Protocol):
    async def search_jobs(self, query: str, limit: int = 30) -> list[dict]: ...
    async def get_job(self, job_id: str) -> dict: ...
    async def get_client_history(self, client_id: str) -> dict: ...
    async def get_connects_balance(self) -> dict: ...
    async def list_messages(self, conversation_id: str = "") -> list[dict]: ...
    async def create_proposal_draft(self, payload: dict) -> dict: ...
    async def submit_proposal(self, payload: dict) -> dict: ...
    async def send_message(self, payload: dict) -> dict: ...


def marketplace():
    from gigbid_core.config import settings
    from mcp_servers.marketplace.adapters.gigsim import GigSimAdapter
    from mcp_servers.marketplace.adapters.local import LocalSimulatorAdapter
    from mcp_servers.marketplace.adapters.upwork_live import UpworkAdapter

    mode = settings().marketplace_mode
    if mode == "local_simulator":
        return LocalSimulatorAdapter()
    if mode == "gigsim":
        return GigSimAdapter()
    if mode == "upwork":
        return UpworkAdapter()
    raise ValueError("Invalid marketplace mode")
