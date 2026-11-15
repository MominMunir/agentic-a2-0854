# X1: evidence-based agency routing

Agency mode evaluates all three personas through Portfolio MCP, measures covered
requirements and selects a member only above the configured minimum fit. It
keeps the selected persona's evidence isolated and drafts in that persona's
profile. The job detail screen exposes a comparison and can analyze with the
recommended member before an existing run is started.

The runner `python -m evaluation.agency_eval` measures routing on the frozen
synthetic job set and writes raw candidates and predictions to
`evaluation/raw/agency.jsonl`, with its summary in `evals/results/agency.json`.
This evaluates skill routing, including no-match cases. Risk and compliance run
after routing; a good skill match does not make an unsafe job acceptable.

The current tie rule is deterministic. There is no evidence this policy improves
real hire rate, and synthetic coverage labels do not capture availability,
collaboration cost or real team voice. Those are explicit limitations.
