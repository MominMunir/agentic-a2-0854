FROM node:24.19.0-alpine AS web
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci --no-fund
COPY apps/web ./
RUN npm run build

FROM python:3.12.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/app/.venv/bin:$PATH HF_HOME=/app/.cache/huggingface
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.12.5 && uv sync --frozen --extra retrieval --no-dev --no-install-project
COPY agent agent
COPY apps/api apps/api
COPY apps/__init__.py apps/__init__.py
COPY gigbid_core gigbid_core
COPY mcp_servers mcp_servers
COPY rag rag
COPY worker worker
COPY simulator simulator
COPY scripts scripts
COPY infra/render_start.py infra/render_start.py
COPY data/synthetic data/synthetic
COPY data/personas data/personas
COPY data/policy_pack data/policy_pack
RUN uv sync --frozen --extra retrieval --no-dev && python scripts/warm_models.py
COPY --from=web /web/dist apps/web/dist
RUN useradd --create-home --uid 10001 gigbid && mkdir -p data/runtime .cache tmp && chown -R gigbid:gigbid /app
USER gigbid
EXPOSE 10000
CMD ["python","infra/render_start.py"]
