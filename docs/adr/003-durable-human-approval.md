# Durable human approval

Status: accepted. Recorded 15 November 2026.

Checkpoint before any proposal, message or Connects effect. Bind approval to the
tenant, action, exact text, screening answers and cost. Recheck evidence and
compliance before execution. Commit local simulator effects, wallet changes
and idempotency records atomically.

This preserves pending decisions across restarts and prevents duplicate local
debits. Replays clear prior approval. Evidence: workflow tests and
`evals/results/deployment_smoke.json`.
