# Strictly free deployment: Render recommendation

Checked against official provider documentation on 2026-11-15. This profile is
for a low-traffic assignment demonstration. It cannot promise uninterrupted
availability or compliance with an always-live grading requirement. No paid
service or trial-to-paid upgrade is included in `render.yaml`.

## Recommended arrangement

| Component | Free placement | Persistence / limit |
|---|---|---|
| React, FastAPI and three MCP surfaces | One Render Free Web Service | Sleeps on idle; local disk is ephemeral |
| Arq worker | Separate supervised process in that same web instance | Stops while the free instance sleeps |
| Application, checkpoints, audit, memory and uploaded text | Neon Free Postgres | External durable storage within its free quotas |
| Queue/locks | Render Free Key Value | In-memory only; DB recovery reconstructs queued work after loss |
| Open vectors | Qdrant Cloud Free cluster | External authenticated vector store within free capacity |
| LLM | Existing Groq Free account/key | Provider rate/token limits apply; no paid upgrade configured |
| Tracing | Saved DB traces; full Phoenix in local Compose | A hosted OTLP collector is optional and needs its own free-account configuration |

The compact container runs the API and worker as separate processes. Agent work
stays outside web requests. Each MCP server remains independently packaged and
mounts at `/portfolio/mcp`, `/marketplace/mcp` or `/workspace/mcp`; bearer tokens
are scoped to the intended server. Only Portfolio access tokens are exposed to
authenticated application users for external read-only MCP hosts.

A local Docker test passed with the exact 512 MiB memory ceiling, real CPU
embeddings, authenticated HTTP MCP, Redis, Postgres and a durable approval interrupt.
The final test measured 465.9 MiB in use and a 472.56 MiB peak; see
`evals/results/free_deployment_smoke.json` for the current observation. The first
default-batch attempt was killed for exceeding memory. The free profile now uses
batches of two, one embedding thread and reduced ONNX allocation. This is tight
headroom for a low-traffic demo, not a load-test or public-host guarantee. Actual
free-host CPU, storage and network behavior still requires deployment verification.

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
2. Create the Neon database. Put the connection string into `DATABASE_URL` with
   the `postgresql+psycopg://` prefix. Use the equivalent `postgresql://` URL for
   `CHECKPOINT_URL`; retain the provider's TLS options in both.
3. Create a Qdrant Free cluster and provide `QDRANT_URL` and `QDRANT_API_KEY`.
4. Supply `OPEN_MODEL_API_KEY`, `TOKEN_ENCRYPTION_KEY`, `REVIEWER_EMAIL` and
   `REVIEWER_PASSWORD` through Render's private environment settings. The
   encryption key must be a Fernet key; bootstrap already creates one locally.
5. Connect the public GitHub repository and create a Blueprint from `render.yaml`.
   Review the proposed resources: exactly one **Free** web service and one **Free**
   Key Value instance, with no Render Postgres database or paid background worker.
6. The starter command derives `APP_URL` from Render's assigned public URL.
   If using a custom domain, set APP_URL explicitly to its HTTPS origin.
7. After the owner approves the deployment, verify login, a real open-model draft,
   SSE, source deletion, an approval, idle wake-up and a restart. Record the exact
   live URL and commit. Account creation/publication/verification are external
   checkpoints and have not been represented as already completed.

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
