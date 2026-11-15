# Marketplace port

Status: accepted. Recorded 15 November 2026.

Use one MarketplacePort interface behind Marketplace MCP. Local simulation,
instructor GigSim and official Upwork adapters share the graph-facing contract.
The graph never receives credentials or calls marketplace APIs directly.

This keeps approval, rate-limit and idempotency checks at a capability boundary.
Live OAuth and tool mappings require account verification. External exactly-once
effects depend on the upstream service's idempotency contract.
