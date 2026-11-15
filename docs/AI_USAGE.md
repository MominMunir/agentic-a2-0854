# AI assistance disclosure

Codex assisted with requirement parsing, architecture, original source code,
synthetic fixtures, tests, measured experiments and documentation in this folder.
The supplied starter kit was read as a reference for interfaces, layout, policies
and sample schemas. Its files were not copied into this repository or modified.
The student must review and be able to explain every component in the viva.

Errors found and corrected during implementation include a LangGraph node/state
name collision, an incompatible checkpoint driver, omitted retrieval metadata,
overly permissive claim detection and a signup redirect race caught by Playwright.
A broad lint command also reached local dependency caches; the environment was
restored from clean downloads and checks were restricted to source directories.

Groq inference is used by GigBid itself and by explicitly labeled research runs.
Model output is never accepted as portfolio truth or as human evaluation labels.
No hidden evaluation set was used, no deadline or commit history was fabricated,
and missing external results are recorded as unavailable.
