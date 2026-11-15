# Strictly free deployment: Render recommendation

Checked against official provider documentation on 2026-11-15. This profile is
for a low-traffic assignment demonstration. It cannot promise uninterrupted
availability or compliance with an always-live grading requirement. No paid
service or trial-to-paid upgrade is included in `render.yaml`.

## Recommended arrangement

| Component | Free placement | Persistence / limit |
|---|---|---|
| React, FastAPI and three MCP surfaces | One Render Free Web Service | Sleeps on idle; local disk is ephemeral |
| Arq worker | Background Arq task sharing the API process | Redis queue; stops while the free instance sleeps |
| Application, checkpoints, audit, memory and uploaded text | Neon Free Postgres | External durable storage within its free quotas |
| Queue/locks | Render Free Key Value | In-memory only; DB recovery reconstructs queued work after loss |
| Open vectors | Qdrant Cloud Free cluster | External authenticated vector store within free capacity |
| LLM | Existing Groq Free account/key | Provider rate/token limits apply; no paid upgrade configured |
| Tracing | Saved DB traces; full Phoenix in local Compose | A hosted OTLP collector is optional and needs its own free-account configuration |

The compact container shares one Python process between the API and background
Arq worker, avoiding duplicate imports under the 512 MiB ceiling. Agent work
stays in Redis-managed background jobs, outside web request handlers. CPU
retrieval runs in a thread so health checks remain responsive. The full Compose
profile retains independent API and worker processes. Each MCP server remains independently packaged and
mounts at `/portfolio/mcp`, `/marketplace/mcp` or `/workspace/mcp`; bearer tokens
are scoped to the intended server. Only Portfolio access tokens are exposed to
authenticated application users for external read-only MCP hosts.

A local Docker test passed with the exact 512 MiB memory ceiling, real CPU
embeddings, authenticated HTTP MCP, Redis, Postgres and a durable approval interrupt.
See `evals/results/free_deployment_smoke.json` for current memory observations.
The initial default-batch attempt exceeded memory. Smaller batches passed a
local test, but cloud testing then exposed another peak: Argon2 sign-in after
embeddings warmed exceeded 512 MiB in the two-process profile. The compact runtime
now shares the worker process and explicitly tests three sign-ins after real
retrieval. Batches remain two, with one embedding thread and reduced ONNX
allocation. Password hashing parameters and embedding weights remain unchanged.
This is a low-traffic demo profile, not a load-test or uptime guarantee.

The revised local test measured 353.2 MiB in use and 432.22 MiB peak, including
three password sign-ins after embedding weights were loaded. Backend checks
cover the embedded worker's startup/shutdown and degraded health state. Blueprint
build filters avoid restarting the app for report, documentation and evaluation
record updates; application/runtime changes remain eligible for automatic builds.
For an explicit update, use **Manual Deploy > Deploy latest commit** in Render.

## Why Render for this project

[Render Free](https://render.com/docs/free) accepts the existing Docker/Python
stack. Free web services sleep after 15 minutes without inbound traffic and take
about a minute to wake. Their disks are ephemeral, free Postgres expires after
30 days, and free Key Value loses its queue on restart. The profile therefore
stores durable application state in external Postgres, and the worker reconciles
queued/stale runs from that database after broker or process loss.

[Neon Free](https://neon.com/pricing) currently advertises a free plan without a
time limit or required credit card. Select Free only, retain the credentials
privately and monitor its compute/storage quotas. This avoids Render's 30-day
database expiry. [Qdrant Cloud](https://qdrant.tech/documentation/cloud/create-cluster/)
provides a free cluster option; choose that option only and keep the API key private.

Vercel can serve the frontend and Python functions. Its newer Daemons beta also
supports continuous workers on Hobby, but the [daemon limits](https://vercel.com/docs/daemons/limits)
include a minimum 1 GiB instance and 420 GB-hours per month. A continuously running
minimum instance would consume that allowance in roughly 17 days (a calculation
from those limits). It is therefore not an unlimited free worker host. We do not
claim that Vercel lacks Python or background-worker support.

## Prepare accounts and secrets

1. Create/select Free accounts on Render, Neon and Qdrant Cloud. Do not select
   paid plans, trial upgrades, paid disks or paid workers.
2. Create the Neon database. In **Connect**, disable **Connection pooling** to
   copy the direct connection string. Put it into `DATABASE_URL` with
   the `postgresql+psycopg://` prefix. Use the equivalent `postgresql://` URL for
   `CHECKPOINT_URL`; retain the provider's TLS options in both.
3. Create a Qdrant Free cluster and provide `QDRANT_URL` and `QDRANT_API_KEY`.
4. Supply `OPEN_MODEL_API_KEY`, `TOKEN_ENCRYPTION_KEY`, `REVIEWER_EMAIL` and
   `REVIEWER_PASSWORD` through Render's private environment settings. The
   encryption key must be a Fernet key; bootstrap already creates one locally.
5. Connect the public GitHub repository and create a Blueprint from `render.yaml`.
   Review the proposed resources: exactly one **Free** web service and one **Free**
   Key Value instance, with no Render Postgres database or paid background worker.
   Repository: `MominMunir/agentic-a2-0854`; branch: `main`; Blueprint path:
   `render.yaml`. Leave the root directory empty. In Render use **New > Blueprint**.
6. The starter command derives `APP_URL` from Render's assigned public URL.
   If using a custom domain, set APP_URL explicitly to its HTTPS origin.
7. After the owner approves the deployment, verify login, a real open-model draft,
   SSE, source deletion, an approval, idle wake-up and a restart. Record the exact
   live URL and commit. See [deployment status](DEPLOYMENT_STATUS.md) for the
   completed instance and recorded public checks.

### Values requested by the Blueprint

| Variable | Value to enter privately |
|---|---|
| `DATABASE_URL` | Direct Neon URL with `postgresql://` replaced by `postgresql+psycopg://` |
| `CHECKPOINT_URL` | Original direct Neon URL beginning `postgresql://` |
| `QDRANT_URL` | Qdrant Free cluster HTTPS endpoint |
| `QDRANT_API_KEY` | Database API key for that cluster, with collection read/write access |
| `OPEN_MODEL_API_KEY` | Existing Groq key in the local private `.env` |
| `TOKEN_ENCRYPTION_KEY` | Existing Fernet key in the local private `.env` |
| `REVIEWER_EMAIL` | Existing reviewer email in the local private `.env` |
| `REVIEWER_PASSWORD` | Existing reviewer password in the local private `.env` |

Keep Neon URL query options, including `sslmode=require`, intact. Copy the URL
itself without a `psql` command or surrounding quote marks. Use a **database API
key** from Qdrant's cluster console, not a Cloud management API key. The app
creates its vector collections, so the key needs the corresponding write access.

The Blueprint supplies Redis and generates `APP_SECRET_KEY`. Leave `APP_URL`
unset so startup uses Render's assigned HTTPS address. Copy only the listed local
values; importing the entire local `.env` would overwrite cloud URLs with local
addresses. Fill the secret fields before clicking **Deploy Blueprint**.

The public Portfolio URL is the same origin plus `/portfolio/mcp`. Sign in, mint
a one-hour Portfolio read token through `/api/portfolio/access-token`, and provide
it privately to the MCP host as `Authorization: Bearer ...`. Do not publish it in
the report, repository or video. Marketplace and Workspace endpoints require
their own internal scope; the Portfolio token cannot access them.

## Optional Vercel frontend

Keep Render as the backend. Once its actual URL exists, run:

```sh
python scripts/configure_vercel.py --backend-url https://your-actual-render-origin
```

The argument must be replaced with the actual deployed origin. This writes a
same-origin `/api` proxy into `apps/web/vercel.json`. Deploy `apps/web` as a Vite
project on Vercel Hobby and set the backend APP_URL to the actual Vercel origin.
The proxy lets session cookies stay on the frontend origin. The generated Vercel
configuration alone does not create a backend or database.

## Explicit limitations

Automatic scouting pauses during Render sleep. Cold starts can exceed the
declared latency budget. Free quotas can suspend services; there is no uptime
guarantee. Real Upwork/GitHub connections still require the owner's credentials
and schema verification. The compact profile is a cost-constrained demonstration,
while local Compose retains the complete independent-service architecture for
reproduction and the viva. Do not use artificial traffic to evade provider idle
policies, and do not describe this free profile as an always-on production SLA.
