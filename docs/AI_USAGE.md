# AI assistance disclosure

Codex assisted with architecture, implementation and documentation across
`agent/`, `rag/`, `mcp_servers/`, `apps/`, `worker/`, `scripts/`, `evaluation/`
and `docs/`. The starter kit was used as an interface reference and left unchanged.

Errors caught during verification included a LangGraph node/state name collision,
an incompatible checkpoint driver, omitted retrieval metadata, overly permissive
claim detection and a sign-up redirect race. Regression tests cover the repairs.
The cloud registration check also exposed 999 database operations during account
setup; batching reduced the local seed count to two and restored public sign-up.

Groq inference is used by GigBid itself and by explicitly labeled research runs.
Model output is never accepted as portfolio truth or as human evaluation labels.
The hidden test set was not accessed. Human evaluation remains uncompleted and
is not represented by generated labels.

Cloud deployment exposed a memory failure missed by the initial local smoke
test: sign-in after embeddings warmed exceeded the free instance's 512 MiB.
The compact profile now shares the Redis/Arq worker with the API process, and
the smoke check repeats sign-in after retrieval. CPU search runs outside the
API event loop with serialized index-cache creation. Password hashing parameters
and model weights were retained. The full Compose profile keeps separate workers.
