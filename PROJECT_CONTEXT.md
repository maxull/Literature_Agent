# PROJECT_CONTEXT.md

Last updated: 2026-03-03

## Project Overview

`Literature_Agent` generates weekly skeletal-muscle literature digests as JSON and serves them in a Shiny application.

## Repository Map

- `README.md`: end-to-end usage instructions.
- `config.yaml`: query, ranking, output, and runtime settings.
- `run_weekly_digest.py`: executable entry script.
- `literature_scout/`: core package (queries, filtering, summarization, pipeline, state handling).
- `reports/weekly_digests/`: digest outputs consumed by the app.
- `shiny_app/app.py`: interactive digest browser.
- `skills/muscle-digest-enricher/`: optional local enrichment skill and validation scripts.
- `tests/`: pipeline and behavior tests.

## Shared Conventions

- Digest outputs follow `weekly_muscle_digest_YYYY-MM-DD.json` naming.
- State and run history are persisted locally via JSON files.
- Sorting and deterministic behavior are preferred for stable diffs and repeatable outputs.

## Subprojects

### Pipeline Core (`literature_scout/`)

- Purpose: fetch, deduplicate, rank, summarize, and serialize digest records.
- Canonical scripts: `run_weekly_digest.py`, `literature_scout/cli.py`, `literature_scout/pipeline.py`.
- Key inputs: `config.yaml`, source APIs, `state_seen.json`.
- Key outputs: digest JSON and run log updates.
- Caveats: source retrieval may partially fail; pipeline should continue while recording failures.

### Digest UI (`shiny_app/`)

- Purpose: provide interactive review of the latest digest with filtering and cluster views.
- Canonical script: `shiny_app/app.py`.
- Key inputs: latest digest in `reports/weekly_digests/`.
- Key outputs: local interactive UI session.
- Caveats: UI expects stable digest keys (coverage, clusters, papers, methods index).

### Enrichment Skill (`skills/muscle-digest-enricher/`)

- Purpose: standardize prose enrichment and validation of digest fields.
- Canonical scripts: `validate_digest_enrichment.py`, `locate_latest_digest.py`.
- Key inputs: latest digest JSON.
- Key outputs: validated enriched JSON.
- Caveats: enrichment must preserve schema and DOI link structure.

## Canonical Vs Legacy Notes

- Canonical output is JSON in `reports/weekly_digests/`; older markdown-only formats are legacy.
- `run_weekly_digest.py` is the preferred execution path over ad-hoc module calls.

## Durable Decisions

- Keep digest generation robust to partial source failures.
- Preserve same-day non-empty digest outputs when reruns produce no summaries.
- Keep enrichment validation in the workflow when edited summaries are introduced.
