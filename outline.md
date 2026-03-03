# Project Outline

`Literature_Agent` is a weekly literature scouting workflow for skeletal-muscle research.

- Collects new literature from configured databases/preprint sources.
- Deduplicates, filters, ranks, and summarizes candidate papers.
- Writes a structured digest JSON to `reports/weekly_digests/`.
- Tracks run state and seen identifiers to avoid reprocessing.
- Serves the latest digest through a Shiny app at `shiny_app/app.py`.

Primary execution path:
- `python run_weekly_digest.py --config config.yaml`
