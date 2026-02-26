---
name: muscle-digest-enricher
description: Use this skill when you need to enrich a generated weekly muscle digest JSON with chapter-style scientific context and paper-level narrative summaries before viewing it in the Shiny app, without calling external LLM APIs.
---

# Muscle Digest Enricher

Use this skill to transform draft digest JSON into publication-style narrative summaries before launching the Shiny app.

## Inputs
- Digest JSON in `reports/weekly_digests/weekly_muscle_digest_YYYY-MM-DD.json`

## Outputs
- Updated digest JSON at the same path with:
  - `clusters.<cluster>.chapter_summary` written in chapter-style prose, anchored to your AMPK example style/length (~300 words, flexible range).
  - `papers[*].discussion_summary` written in chapter-style prose, anchored to your AMPK example style/length (~300 words, flexible range).
  - DOI-first links preserved in `doi_url`.

## Required writing style
- Natural scientific prose, not bullet format.
- Start with background science, then integrate the paper's new contribution.
- Include evidence/method framing language in each paper-level `discussion_summary`.
- Keep claims bounded to abstract/metadata evidence.

## Required workflow
1. Find latest digest JSON with:
   - `python skills/muscle-digest-enricher/scripts/locate_latest_digest.py`
2. Read JSON and rewrite every cluster chapter summary:
   - example-anchored chapter style (~300 words, not a hard sentence rule)
   - background -> integration of new findings
3. Rewrite every paper `discussion_summary`:
   - example-anchored chapter style (~300 words, not a hard sentence rule)
   - background -> methods/evidence -> added value
4. Ensure DOI-first links:
   - If `doi` exists, `doi_url` must be `https://doi.org/<doi>`.
5. Run validator:
   - `python skills/muscle-digest-enricher/scripts/validate_digest_enrichment.py <path-to-json>`
6. If validation fails, fix and rerun validator.

## Guardrails
- Do not invent experiments or conclusions absent from the paper data.
- If abstract is missing, state uncertainty explicitly.
- Do not remove existing fields from JSON.
