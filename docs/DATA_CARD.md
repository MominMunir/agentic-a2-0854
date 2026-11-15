# Data card

## Real historical job records

Two approved sources were downloaded through Kaggle's API using an existing
private credential file. No website was scraped.

| Dataset | Attribution / metadata license | Selection rationale |
|---|---|---|
| [Upwork job postings 2024](https://www.kaggle.com/datasets/asaniczka/upwork-job-postings-dataset-2024-50k-records), asaniczka | ODC Attribution License (ODC-By) | Job descriptions, dates and disclosed budget fields |
| [Upwork freelance jobs 60k](https://www.kaggle.com/datasets/ahmedmyalo/upwork-freelance-jobs-60k), ahmedmyalo | Apache 2.0 | A second historical source with different schemas and client/payment fields |

Dataset license statements come from the archived Kaggle metadata. They do not
establish rights to republish every third-party job description. Raw archives
and normalized job text are excluded from the public release; recipients
reproduce the import under the source terms. Attribution and archive SHA-256
hashes remain in `data/real_manifest.json`. No real client messages or personal
portfolio records are included.

`scripts/preprocess_kaggle.py` reads CSV members without extracting executable
files, validates nonempty title/description, recognizes selected technical
skills, hashes whitespace-normalized title+description for deduplication, keeps
fixed-price jobs and caps each source subset. Hourly rates are not converted into
invented fixed project prices. Source URL/date/row/license/dataset are retained.
Emails and phone-like strings are masked before import. Budget bounds are set to
the single disclosed fixed budget when only one price exists.

Records are written only to `data/processed/real/`. `provenance=kaggle` and
`synthetic=false` are mandatory. Unknown client history stays unknown. A default
duration and Connects estimate allow local workflow exercises; both have explicit
estimated flags and are not presented as observed dataset facts. The local
simulator remains a simulation even when a job description is historical.

The other four approved sources are not imported: the selected two cover the
current job schema, while contracts/earnings/churn rows cannot supply verified
portfolio evidence, client conversations or causal hiring outcomes. This avoids
merging unrelated entities as though they belonged to one freelancer. The
fetch command accepts all six approved IDs for future documented extensions.

## Original synthetic corpus

`scripts/generate_data.py`, seed 4016, creates three personas, domain-specific
case studies, README/code excerpts, reviews, labeled proposal histories, client
histories, conversations and job posts with negative/injection examples. Counts
are recorded in `data/synthetic/manifest.json`. Every item carries
`provenance=synthetic`, `synthetic=true` and a synthetic source URI. Files live
under `data/synthetic/` or explicitly marked persona/evaluation directories.
These are original generated fixtures, not copied starter-kit records.

Each evidence item has ID, persona, type, project, skills, date, industry, outcome,
source and provenance. The development/holdout boundary is by industry: retail,
healthcare, finance and education are development; logistics and energy are
holdout. No hidden test is present. Template-derived gold evidence includes all
item types for the designated project/domain. The gold labels are not independent
human annotations, and repeated text makes the task easier in some ways and
ambiguous in others. Confidence intervals from these fixtures would not measure
real-world population uncertainty.

## User and GitHub evidence

PDF/text/Markdown/JSON/code loaders create stable content-hash chunk IDs with
overlap. Re-uploading identical bytes updates the same IDs. Scanned PDFs with no
text fail clearly. Uploads are limited to 5 MB and stored in the tenant's database;
their text does not become public source. The official GitHub MCP read tool can
ingest a selected README or code path with its repository URL as provenance.
User uploads are tagged `user_upload`; GitHub reads use `github_mcp`. Both are
kept separate from synthetic records. Uploaded claims are unverified until the
owner validates the source; retrieval is not proof that a source itself is true.

## Missing instructor assets

The instructor's GigSim package/API, full personas, development labels, hidden
set and November 2 policy update were not supplied. The user confirmed they were
unavailable. Nothing in the evaluation is labeled as an instructor or hidden-test
result. Local rule-based replies are not evidence of GigSim reply or hire rates.
