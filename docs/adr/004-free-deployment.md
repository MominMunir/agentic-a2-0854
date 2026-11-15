# Free deployment

Status: accepted. Recorded 15 November 2026.

Use one Render Free web service, Render Free Key Value, Neon Free and Qdrant Free.
Share the API process with an asynchronous Arq worker to fit the memory ceiling.
The full Docker Compose stack retains independent workers.

The initial compact deployment exhausted memory after retrieval and sign-in.
The repaired regression check peaked at 432.22 MiB under a 512 MiB limit.
Free sleep and provider quotas remain availability constraints. Evidence:
`evals/results/free_deployment_smoke.json` and `registration.json`.
