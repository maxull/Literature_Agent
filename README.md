# Weekly Skeletal Muscle Literature Scout

This project runs a weekly literature scan across peer-reviewed and preprint sources, filters for skeletal-muscle relevance, ranks by mechanistic depth/novelty/translational value, and writes a structured Markdown digest:

- `weekly_muscle_digest_YYYY-MM-DD.md`

## What It Does

- Searches every run:
  - `PubMed` (broad query + journal-tier watchlist query)
  - `bioRxiv`
  - `medRxiv`
  - `sportRxiv` (via Crossref index)
  - Optional `arXiv`
- Applies two-stage relevance:
  - Stage 1 rule-based include/exclude
  - Stage 2 weighted ranking (mechanistic depth, novelty, translational relevance, technical innovation, journal tier)
- Produces required sections:
  - Itinerary
  - Coverage
  - Highlights (Top 3-5)
  - Paper summaries (fixed template)
  - Abstracts (Full)
- Maintains state:
  - `state_seen.json`
  - `run_log.json`

## Journal Tiers

The search/ranking is configurable via `config.yaml`:

- `journal_tiers.tier_1`: always prioritized core skeletal-muscle and high-signal journals.
- `journal_tiers.tier_2`: broad high-impact and adjacent mechanistic venues.
- `journal_tiers.tier_3`: optional/watchlist journals where relevance can be inconsistent.
- `active_journal_tiers`: choose which tiers are actively queried.
- `journal_tier_weights`: rank boost per tier.

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

## GitHub Actions (Manual Run)

This repo includes [`run_digest.yml`](/Users/maxullrich/Documents/GitHub/Literature_Agent/.github/workflows/run_digest.yml).

To run once:
1. Open your repo on GitHub.
2. Go to `Actions` -> `Run Muscle Digest`.
3. Click `Run workflow`.
4. Optionally set `days_back`.
5. Download the `weekly-muscle-digest` artifact from the completed run.

## Notes

- The summarization layer is intentionally conservative and only uses source metadata/abstracts.
- If a source fails, the run still produces a report and logs failures under Coverage and `run_log.json`.
