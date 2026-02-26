# Muscle Litterature Explorer - by Max Ullrich

This repository does three things:
1. Searches literature sources and builds a digest JSON.
2. Lets Codex enrich summaries using a local skill workflow.
3. Serves an interactive Shiny app for exploration.

Primary output file:
- `reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.json`

## 1) One-Time Setup (in terminal)

```bash
cd "your path here (without quotation marks)"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 2) Configure the Search

Edit:
- `config.yaml`

Important knobs:
- `days_back`: how far back to search (default 7)
- `max_candidates_per_source`: retrieval cap per source
- `max_summaries_total`: summary cap; use `0` for unlimited
- `include_keywords`: positive search terms
- `exclude_keywords`: terms to filter out noisy papers
- `preferred_topics`: ranking boost topics
- `methods_keywords`: methods index vocabulary shown in the app
- `active_journal_tiers`: which journal tiers are actively used

### Change timeframe examples

7 days:
```yaml
days_back: 7
```

14 days:
```yaml
days_back: 14
```

30 days:
```yaml
days_back: 30
```

### Edit search terms

Add/remove terms in:
- `include_keywords`
- `exclude_keywords`
- `preferred_topics`
- `methods_keywords`

## 3) Generate Digest JSON (Local)

```bash
cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate
python run_weekly_digest.py --config config.yaml
```

This writes/updates:
- `reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.json`

## 4) Enrich Summaries with Codex Skill (No API Required)

Skill path:
- `skills/muscle-digest-enricher/SKILL.md`

In Codex chat, paste this prompt:

```text
Use skills/muscle-digest-enricher/SKILL.md as the active instructions for this task.

Find the latest digest JSON in reports/weekly_digests/.
Edit that JSON in place:
- Rewrite every clusters.<cluster>.chapter_summary in chapter-style prose anchored to the AMPK example style/length.
- Rewrite every papers[*].discussion_summary in the same style.
- Preserve all fields and keep DOI-first links (doi_url must be https://doi.org/<doi> when doi exists).

After editing, run:
python skills/muscle-digest-enricher/scripts/validate_digest_enrichment.py <path-to-json>

If validation fails, fix and rerun until it passes.
```

## 5) Validate Enriched Digest

Locate latest digest:

```bash
python skills/muscle-digest-enricher/scripts/locate_latest_digest.py
```

Validate:

```bash
python skills/muscle-digest-enricher/scripts/validate_digest_enrichment.py reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.json
```

## 6) Launch the Shiny App

```bash
cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate
shiny run --reload shiny_app/app.py
```

Open:
- `http://127.0.0.1:8000`

Stop app:
- `Ctrl + C` in the terminal running Shiny.

## 7) Optional: Run via GitHub Actions

Workflow file:
- `.github/workflows/run_digest.yml`

Steps:
1. GitHub -> Actions -> `Run Muscle Digest`
2. Click `Run workflow`
3. Set `days_back` if needed (e.g., 14 or 30)
4. Run
5. Pull local updates:

```bash
git pull
```

## 8) Typical End-to-End Local Commands

```bash
cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate
python run_weekly_digest.py --config config.yaml
python skills/muscle-digest-enricher/scripts/locate_latest_digest.py
# Use Codex skill prompt to rewrite summaries here
python skills/muscle-digest-enricher/scripts/validate_digest_enrichment.py reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.json
shiny run --reload shiny_app/app.py
```
