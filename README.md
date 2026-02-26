# Weekly Skeletal Muscle Literature Scout

This project runs a weekly literature scan across peer-reviewed and preprint sources, filters for skeletal-muscle relevance, ranks by mechanistic depth/novelty/translational value, and writes a structured Markdown digest:

- `weekly_muscle_digest_YYYY-MM-DD.md`

## What It Does

- Searches every run:
  - `PubMed`
  - `bioRxiv`
  - `medRxiv`
  - `sportRxiv` (via Crossref index)
- Applies two-stage relevance:
  - Stage 1 rule-based include/exclude
  - Stage 2 weighted ranking
- Produces required sections:
  - Itinerary
  - Coverage
  - Highlights (Top 3-5)
  - Paper summaries (fixed template)
  - Abstracts (Full)
- Maintains state:
  - `state_seen.json`
  - `run_log.json`

## Quick Start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Edit [`config.yaml`](/Users/maxullrich/Documents/GitHub/Literature_Agent/config.yaml).

3. Run:

```bash
python run_weekly_digest.py --config config.yaml
```

## Weekly Automation Example

Run every Monday at 08:00 local time:

```bash
0 8 * * 1 cd /Users/maxullrich/Documents/GitHub/Literature_Agent && /usr/bin/python3 run_weekly_digest.py --config config.yaml
```

## Notes

- The summarization layer is intentionally conservative and only uses source metadata/abstracts.
- If a source fails, the run still produces a report and logs failures under Coverage and `run_log.json`.
