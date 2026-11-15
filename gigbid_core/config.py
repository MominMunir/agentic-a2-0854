from functools import lru_cache
import os
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

SOURCE_ROOT = Path(__file__).resolve().parents[1]
# A wheel can read an existing application's database while keeping its caches
# and SQLite files in a caller-owned directory rather than site-packages.
ROOT = Path(os.environ.get("GIGBID_HOME", str(SOURCE_ROOT))).resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")
    app_env: str = "development"
    app_url: str = "http://localhost:5173"
    app_secret_key: str = ""
    token_encryption_key: str = ""
    database_url: str = "sqlite:///data/runtime/gigbid.db"
    checkpoint_url: str = "sqlite:///data/runtime/checkpoints.db"
    redis_url: str = "redis://localhost:6379/0"
    executor: str = "local"
    marketplace_mode: str = "local_simulator"
    gigsim_base_url: str = "http://localhost:8081"
    gigsim_api_token: str = ""
    mcp_transport: str = "stdio"
    portfolio_mcp_url: str = "http://portfolio:8101/mcp"
    marketplace_mcp_url: str = "http://marketplace:8102/mcp"
    workspace_mcp_url: str = "http://workspace:8103/mcp"
    mcp_stdio_tenant: str = ""
    model_profile: str = "open"
    inference_mode: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    open_model_base_url: str = ""
    open_model_api_key: str = ""
    embedding_backend: str = "fastembed"
    embedding_batch_size: int = 16
    embedding_threads: int = 2
    embedding_low_memory: bool = False
    reranker_backend: str = "flashrank"
    rag_variant: str = "v0"
    match_query_mode: str = "whole_job"
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    mount_mcp_servers: bool = False
    serve_frontend: bool = False
    portfolio_public_url: str = ""
    worker_concurrency: int = 2
    embedded_worker: bool = False
    otel_exporter_otlp_endpoint: str = ""
    phoenix_api_key: str = ""
    upwork_mcp_url: str = "https://mcp.upwork.com/mcp"
    upwork_client_id: str = ""
    upwork_redirect_uri: str = "http://localhost:8000/api/accounts/upwork/callback"
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/"
    github_token: str = ""

    def require_secrets(self):
        if len(self.app_secret_key) < 32 or not self.token_encryption_key:
            raise RuntimeError("Run python scripts/bootstrap.py to create private local configuration.")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()


def policy() -> dict:
    return yaml.safe_load((SOURCE_ROOT / "agent/config.yaml").read_text(encoding="utf-8"))
