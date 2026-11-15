# Independent annotation protocol

`judge_calibration.csv` contains 30 actual model drafts with blank human/judge
columns. Architecture/job keys are separate. Ask a human who did not generate the
drafts to score them before viewing model ratings or the key. Score 1 (unusable or
unsupported), 2 (major repair), 3 (adequate), 4 (strong), or 5 (excellent), considering
specificity, substantiated experience, relevance, policy compliance and clarity.
The same rubric must be used by an independently run judge; store its model,
prompt, returned usage and raw outputs. No calibrated judge result exists yet.

After 30 genuine paired labels, run:

```sh
python -m evaluation.human_panel calibration --input evaluation/annotations/judge_calibration.csv
```

`blind_pairwise.csv` pairs actual ReAct and alternate open-profile graph drafts
where both were available. Randomized A/B identities are in `pairwise_key.json`;
keep that file away from raters. Ask at least three independent raters to provide
`rater` and `preferred` (`a`, `b`, or `tie`). Duplicate each pair for each rater.
Do not infer a preference from model scores or fill blank human cells automatically.

```sh
python -m evaluation.human_panel pairwise --input evaluation/annotations/blind_pairwise.csv
```

The simple sign test decodes strategies but treats observations independently;
multiple raters per job need a clustered analysis before inferential claims.
These packets are preparation for real evaluation, not completed human results.
