FROM python:3.12.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY agent agent
COPY apps apps
COPY gigbid_core gigbid_core
COPY mcp_servers mcp_servers
COPY rag rag
COPY worker worker
COPY simulator simulator
COPY scripts scripts
COPY data/synthetic data/synthetic
COPY data/personas data/personas
COPY data/policy_pack data/policy_pack
RUN pip install --no-cache-dir uv==0.12.5 && uv sync --frozen --extra retrieval --no-dev
RUN useradd --create-home --uid 10001 gigbid && mkdir -p data/runtime .cache tmp && chown -R gigbid:gigbid /app
USER gigbid
ENV PATH="/app/.venv/bin:$PATH" HF_HOME=/app/.cache/huggingface
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
