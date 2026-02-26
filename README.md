# Skeletal Muscle Literature Explorer

This project builds weekly digest JSON files and serves them in an interactive Shiny app.

Primary output:
- `reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.json`

## Local Workflow (No API Integration)

1. Generate digest JSON (draft summaries):

```bash
python run_weekly_digest.py --config config.yaml
```

2. Use Codex skill to enrich summaries in JSON (chapter-style prose):
- Skill path in repo: `skills/muscle-digest-enricher`
- Follow instructions in [`SKILL.md`](/Users/maxullrich/Documents/GitHub/Literature_Agent/skills/muscle-digest-enricher/SKILL.md)

3. Validate enriched JSON:

```bash
python skills/muscle-digest-enricher/scripts/locate_latest_digest.py
python skills/muscle-digest-enricher/scripts/validate_digest_enrichment.py <path-to-json>
```

4. Run Shiny app:

```bash
shiny run --reload /Users/maxullrich/Documents/GitHub/Literature_Agent/shiny_app/app.py
```

## Shiny App Features

- Separate tab for each thematic cluster.
- Cluster chapter summary in example-anchored chapter style (~300-word narrative) at top of each tab.
- Highlighted papers with discussion-style summaries.
- DOI-first links.
- Methods keyword search across all clusters and a dedicated Methods Index tab.

## Skill Package

Skill folder:
- [`skills/muscle-digest-enricher/SKILL.md`](/Users/maxullrich/Documents/GitHub/Literature_Agent/skills/muscle-digest-enricher/SKILL.md)

Helper scripts:
- [`locate_latest_digest.py`](/Users/maxullrich/Documents/GitHub/Literature_Agent/skills/muscle-digest-enricher/scripts/locate_latest_digest.py)
- [`validate_digest_enrichment.py`](/Users/maxullrich/Documents/GitHub/Literature_Agent/skills/muscle-digest-enricher/scripts/validate_digest_enrichment.py)

## GitHub Actions

Workflow:
- [`run_digest.yml`](/Users/maxullrich/Documents/GitHub/Literature_Agent/.github/workflows/run_digest.yml)

Manual run writes/commits updated digest JSON, run log, and state files.
