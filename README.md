# Weekly Skeletal Muscle Literature Scout

This project runs a weekly literature scan across peer-reviewed and preprint sources, filters for skeletal-muscle relevance, ranks by mechanistic depth/novelty/translational value, and writes a structured Markdown digest.

Default report location:
- `reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.md`

## What It Does

- Searches every run:
  - `PubMed` (broad theme query + tiered journal watchlist queries)
  - `bioRxiv`
  - `medRxiv`
  - `sportRxiv` (via Crossref index)
  - Optional `arXiv`
- Applies two-stage relevance:
  - Stage 1 rule-based include/exclude
  - Stage 2 weighted ranking (mechanistic depth, novelty, translational relevance, technical innovation, journal tier)
- Writes narrative-style summaries (less bullet-heavy) and groups papers by thematic clusters.
- Adds a methods keyword index for document search.
- Adds best-available key visual links for highlights and each paper entry.
- Maintains state:
  - `state_seen.json`
  - `run_log.json`

## LLM Summaries in GitHub Actions

The pipeline can use an LLM directly in CI.

1. In GitHub, set repository secret `OPENAI_API_KEY`.
2. Keep `use_llm_summaries: true` in [`config.yaml`](/Users/maxullrich/Documents/GitHub/Literature_Agent/config.yaml).
3. Run the workflow manually (`Actions` -> `Run Muscle Digest` -> `Run workflow`).

If no API key is set, the run automatically falls back to deterministic non-LLM summaries.

## Journal Tiers

The search/ranking is configurable in `config.yaml`:

- `journal_tiers.tier_1`: always-prioritized core journals.
- `journal_tiers.tier_2`: broad high-impact and adjacent mechanistic venues.
- `journal_tiers.tier_3`: optional/watchlist journals.
- `active_journal_tiers`: which tiers are actively queried.
- `journal_tier_weights`: ranking boost by tier.

## Quick Start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Edit config:

- [`config.yaml`](/Users/maxullrich/Documents/GitHub/Literature_Agent/config.yaml)

3. Run:

```bash
python run_weekly_digest.py --config config.yaml
```

## GitHub Actions (Manual Run)

Workflow file:
- [`run_digest.yml`](/Users/maxullrich/Documents/GitHub/Literature_Agent/.github/workflows/run_digest.yml)

Run once:
1. Open repo on GitHub.
2. Go to `Actions` -> `Run Muscle Digest`.
3. Click `Run workflow`.
4. Optionally override `days_back`.
5. Workflow commits outputs directly into the repo:
   - `reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.md`
   - `run_log.json`
   - `state_seen.json`
