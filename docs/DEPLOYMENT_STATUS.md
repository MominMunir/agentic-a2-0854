# Public deployment status

- Web app: https://gigbid-wr80.onrender.com
- Portfolio MCP: https://gigbid-wr80.onrender.com/portfolio/mcp
- Source: https://github.com/MominMunir/agentic-a2-0854
- Current deployed revision: `dafaee187b70ea2ed049422d2badc78eb3ac976d`
  (registration fix verified on the public app).
- Full backend/MCP/storage verification revision:
  `09dbf7627a12fe4400d899b4f558eee96078e155`.
- Plans checked in the dashboards: Render web **Free**, Render Key Value **Free**,
  Neon **Free**, and Qdrant **Free**. No paid plan or add-on was selected.

The public check in `evals/results/public_deployment.json` verifies reviewer
login, the saved actual-model draft, authenticated MCP retrieval, rejection of
missing/wrong-scope tokens, three sign-ins after retrieval, the Neon run and its
11 checkpoints, and the authenticated Qdrant collection. The pending draft is
synthetic and was not submitted. Its initial creation used Groq 20b/120b models;
the saved approval survived runtime restarts and the memory-fix deployment.

The later font update raises all explicit UI text sizes by two pixels. The
frontend build and six browser journeys passed, and the live Proposal studio
was checked after Render reported the new revision Live. The base is now 16 px
and its main heading 34 px. The same saved draft remains awaiting approval.
See `evals/results/ui_font_update.json`; this UI check is separate from the
earlier full backend verification and does not claim a new model experiment.

Registration was subsequently repaired by batching starter-data inserts and
running synchronous registration outside the main event loop. The local seed
diagnostic fell from 999 statements to two. All 37 backend tests and six browser
journeys passed. A fresh public account registered in 2.26 seconds, logged in,
received 330 evidence records and three messages, and had 120 simulated Connects
with none spent. Four health checks completed during registration, with a
maximum observed response time of 0.89 seconds. Duplicate registration returned
409, cross-tenant access to the reviewer run returned 404, and the original
reviewer draft remained unchanged and awaiting approval. No proposals/messages
were sent. See `evals/results/registration.json` and `registration_local.json`.

The original two-process compact profile exceeded 512 MiB when sign-in allocated
Argon2 memory after embeddings warmed. Sharing the background queue worker with
the API removed duplicate runtime overhead. The revised local 512 MiB test
peaked at 432.22 MiB and includes three sign-ins after warm-up; the same public
checks passed after rollout. The full Compose stack keeps separate workers.

Free services can sleep or exhaust quotas. This is a verified low-traffic demo,
not an uptime or load guarantee. Portfolio is an authenticated MCP protocol
endpoint; visiting it without a bearer token does not display a normal webpage.
Sign in to the app's Settings to mint a one-hour Portfolio read token.

Reviewer credentials and cloud connection strings are stored only in ignored
private files and provider secret settings. Share reviewer access privately in
Classroom. The article file and recording script are ready; separate blog
publication, demo recording, instructor assets and independent human labels
remain external work.

The owner confirmed the submission deadline was extended to midnight PKT at the
end of November 15, 2026. See `docs/SUBMISSION_GUIDE.md` for the complete audit,
course-concept explanation and submission/viva checklist.
