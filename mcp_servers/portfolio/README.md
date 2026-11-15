# GigBid Portfolio MCP

A read-only evidence server built with the official MCP Python SDK. It exposes
`search_evidence(requirement, k, filters)`, `get_case_study(id)` and `list_skills()`,
case/proposal resource templates, and a screening-answer prompt. Evidence carries
source, date, persona, type, skills, project, industry, outcome and provenance.

## Install and use from source

Clone [the public source](https://github.com/MominMunir/agentic-a2-0854),
then `uv sync --frozen --extra retrieval`.
Run bootstrap and seed with your own environment credentials. To expose only
your account's evidence to a local MCP host, set `MCP_STDIO_TENANT` to your user ID
from `/api/auth/me`, and launch:

```sh
uv run gigbid-portfolio
```

The command is registered in the package and can also be installed from a built
wheel. It does not grant access to another tenant or submit marketplace actions.
Create your own evidence by uploading files in the application before using it.
For an installed wheel, set `GIGBID_HOME` to a writable directory containing your
private `.env`, with `DATABASE_URL` pointing to the application's existing data.
Policy and prompts are packaged assets; caches and SQLite files stay in that home.

## Docker distribution

```sh
docker compose up --build -d postgres redis qdrant portfolio
```

Use the shared private configuration and run the seed service once. The local
HTTP endpoint is `http://localhost:8101/mcp`. It requires a short-lived per-tenant
bearer token. `python scripts/mcp_token.py` writes a token to the ignored private
folder for local host configuration; never commit or publish the token.

For a local host that supports stdio, configure its command as `uv`, arguments
`run --directory /absolute/path/to/gigbid gigbid-portfolio`, and the tenant ID in
its environment. Read-only does not mean public data: HTTP always authenticates.

## Publish and inspect

The public authenticated endpoint is
`https://gigbid-wr80.onrender.com/portfolio/mcp`. Sign in to the app and obtain a
one-hour read token from Settings for your MCP host. Source/Docker/wheel install
paths are available; a PyPI registry package has not been published. Test locally with:

```sh
npx @modelcontextprotocol/inspector uv run gigbid-portfolio
```

Set the tenant environment in the host/Inspector configuration. In Inspector,
capture the tools list, a successful `search_evidence`, the case resource and the
prompt. The official Inspector was exercised against the stdio server:

- [Tools list](../../docs/images/mcp-inspector-tools.png)
- [Successful evidence search](../../docs/images/mcp-inspector-search.png)
- [Resource templates](../../docs/images/mcp-inspector-resources.png)
- [Screening prompt](../../docs/images/mcp-inspector-prompts.png)

These are captures of the actual Inspector session, separate from app screenshots.
The free Render profile exposes authenticated Portfolio at `/portfolio/mcp`;
see [free deployment instructions](../../docs/FREE_DEPLOYMENT.md).

The public deployment must terminate TLS and keep the database private. The MCP
tool-schema snapshot and HTTP-auth tests run in CI. The original synthetic corpus
is a demonstration, not a freelancer's verified work history.
