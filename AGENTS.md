# AGENTS.md

Read `PROJECT_CONTEXT.md` before taking any action.

## Scope

This repository builds and serves a weekly skeletal-muscle literature digest:

- Python ingestion/ranking/summarization pipeline in `literature_scout/`.
- JSON digest outputs in `reports/weekly_digests/`.
- Interactive Shiny app in `shiny_app/`.
- Optional enrichment workflow in `skills/muscle-digest-enricher/`.

## Context Rules

- Use `PROJECT_CONTEXT.md` for changing operational details.
- Keep `AGENTS.md` for stable rules and guardrails.
- Prefer explicit file paths over implicit assumptions.

## Coding And Tooling Policy

- Optimize for readability and runtime performance.
- Add concise comments for non-obvious logic.
- Keep the digest schema stable unless coordinated updates are made to parser/UI consumers.
- For Python edits, preserve compatibility with Python 3.10+.

## Data And Output Rules

- Configuration source of truth: `config.yaml`.
- State files: `state_seen.json`, `run_log.json`.
- Primary output: `reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.json`.
- Do not commit secrets or API tokens.

## Runtime Policy

- Canonical pipeline entry point: `python run_weekly_digest.py --config config.yaml`.
- App launch command: `shiny run --reload shiny_app/app.py`.
- Validate enriched digests before publishing when enrichment is used.

## Technical Invariants

- Deduplication priority stays DOI > PMID > preprint identifier.
- Keep DOI-first links when DOI is present (`https://doi.org/<doi>`).
- Preserve guardrail behavior that avoids replacing a same-day non-empty digest with an empty rerun.

## Maintenance Rule

When durable process knowledge changes, update both:

- `AGENTS.md` for stable policy.
- `PROJECT_CONTEXT.md` for current facts.
