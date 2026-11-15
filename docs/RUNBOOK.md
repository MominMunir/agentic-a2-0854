# Runbook and publication instructions

## Local development on Windows

From the `gigbid` directory, use Python 3.12 and Node 24:

```powershell
uv sync --frozen --extra dev --extra retrieval
uv run python scripts/bootstrap.py
uv run python scripts/generate_data.py
# Add OPEN_MODEL_API_KEY privately to .env. Never commit this file.
uv run python scripts/seed.py
uv run python scripts/warm_models.py
$env:MCP_TRANSPORT='memory'
uv run uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd apps/web
npm ci
npm run dev
```

Open `http://localhost:5173`. Reviewer credentials come from environment variables
and are saved only in the ignored `.private/reviewer.txt` during bootstrap.
Registration also creates an isolated account with synthetic demonstration
evidence. Choosing "My own portfolio" retrieves only own-profile uploads.

## Docker deployment, locally

Start Docker Desktop, then `docker compose up --build -d`. The root compose file
includes `infra/docker-compose.yml`. Bootstrap generates the required private
database and simulator secrets. Open `http://localhost:8080`.

The stack contains web, API, Redis/Arq worker, Portfolio/Marketplace/Workspace MCP,
the explicitly labeled local simulator, Postgres, Redis, Qdrant, Ollama and
Phoenix. Only web is exposed broadly. Portfolio and Phoenix ports bind to local
loopback for inspection. Database/vector/broker and write-capable MCP services
stay on the private Compose network.

Groq is selected by default. For local open inference set `INFERENCE_MODE=ollama`
and `MODEL_PROFILE=ollama`, then run:

```sh
docker compose exec ollama ollama pull qwen3:0.6b
docker compose exec ollama ollama pull qwen3:4b
docker compose restart api worker
```

## Public deployment checkpoint

For the user's strictly free requirement, use the prepared
[Render/Neon/Qdrant profile](FREE_DEPLOYMENT.md). The VPS instructions below
describe the full stack for an already provisioned host; they do not provision
or recommend a paid service. Free Render sleeps and cannot promise always-live access.

External hosting requires the user's selected host/domain and authorization.
No public deployment is implied by a local URL. On an authorized Linux VPS:

1. Install Docker Engine and Compose; provision persistent disk and adequate RAM.
2. Clone the clean public repository, run bootstrap/seed, and provide the Groq key
   and reviewer password through environment/secrets management.
3. Set `DEPLOY_ENV=production`, `PUBLIC_APP_URL=https://your-app-domain`, and the
   matching Upwork callback URL. Pin `PHOENIX_IMAGE` to a reviewed immutable tag or
   digest for that deployment; the default tag is a development convenience.
4. Run Compose and put Caddy in front of web and Portfolio using the example
   hostnames in `infra/Caddyfile.example`. Configure DNS and TLS for real domains.
5. Keep Marketplace/Workspace, Postgres, Redis, Qdrant, Phoenix and Ollama private.
   Do not publish their ports. Set HTTPS-only session cookies in production.
6. Test reviewer login, uploads, SSE, an approval and an outage from another
   device. Verify TLS, storage persistence, backup/restore and a restart/resume.
7. Keep the application and Portfolio server running until grades are released.
   Record exact deployment revision, public URLs and a successful access check.

Use `docker compose logs --tail=100 api worker portfolio marketplace` for diagnosis.
Logs mask PII and omit tokens. Database backups include private user data and must
not be committed. Back up Postgres and the encryption key separately; losing the
key makes stored OAuth tokens unrecoverable. Do not use `down -v` on a deployed
stack, because that deletes persistent volumes.

## Public GitHub repository: steps required by the PDF

The public repository must contain this project's required directory structure.
Use this folder as the repository root; do not upload the containing workspace or
the reference starter kit. GitHub Actions needs no paid API key for smoke tests.

```sh
python scripts/repository_checks.py
git init
git branch -M main
git add .
git status --short
git diff --cached --stat
# Inspect the staged names: no .env, .private, runtime DB, cache or raw dataset.
git commit -m "Implement and evaluate GigBid"
gh auth login
gh repo create gigbid --public --source=. --remote=origin --push
```

If `gh` is unavailable, create an empty public repository on GitHub, then add its
remote URL and push `main`. Authentication and publication are user checkpoints.
Never enter a token into a tracked file, README, screenshot or remote URL.

The PDF says the final commit must precede November 12, 2026, 11:59 PM PKT, and
late commits are ignored. This work began after that date. Do not alter commit
timestamps or imply an on-time submission; obtain any deadline exception from
the instructor. The final submission needs the public web URL, repository,
report PDF, recorded demo video, installable/published Portfolio MCP and published
article link. Share reviewer credentials only in a private Classroom comment.

## Approval, recovery and incident exercises

Analyze a safe synthetic job and wait for approval. Restart API/worker. The pending
checkpoint remains. Approve once; the local effect ledger ensures one wallet
debit even if execution is retried. `tests/integration/test_workflow.py` reopens
the disk checkpointer and verifies this contract.

For a service outage, stop Marketplace locally. A run transitions to retry queued
or needs attention with its error in the UI. Restore the service and retry saved
work. Arq retries are bounded; the Settings/Run screens never claim work was sent
if no result was persisted. Checkpoint history is exposed per authenticated run.

Saved-search scouting checks every 15 minutes but only polls a given search when
its interval expires: two hours in simulator mode and four hours in live mode.
The REST adapter caps local request windows below the configured upstream limit,
honors bounded Retry-After delays and queues on rate limits. Actual instructor
limits must replace the development assumptions once supplied.

## Live Upwork and GitHub

Only official remote MCP endpoints are used. Upwork connection uses discovery,
PKCE/state validation and encrypted per-user access/refresh tokens. Discover the
available tools in `/api/accounts/upwork/tools`, verify their official schemas,
then save explicit read/draft tool mappings through the authenticated tool-map
endpoint. Missing mappings fail closed. Do not set live mode until the account
flow and mappings have been checked; no Upwork account was supplied for this
project's tests. Approved live writes create drafts for final platform confirmation.

Set `GITHUB_TOKEN` privately to enable `/api/accounts/github/ingest` for a selected
repo file. The client requests read-only tools. Portfolio content never grants
authority to run repository code. Both third-party integrations require account
credentials and remain unverified against user accounts until connected.
