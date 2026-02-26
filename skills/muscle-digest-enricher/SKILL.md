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
- Specificity first: foreground concrete details from metadata/abstract before general interpretation.
- Start with focused background science, then integrate the paper's new contribution.
- Include evidence/method framing language in each paper-level `discussion_summary`.
- Keep claims bounded to abstract/metadata evidence.
- End each summary with a brief high-level interpretation of implications (1-2 sentences max).

## Specificity rules (mandatory)
- Do not reuse templated openers across papers or clusters.
- Avoid redundant stems such as `Prior work has established that Prior literature...`.
- Avoid empty phrases (`adds value`, `refines biology`, `translational relevance`) unless immediately followed by specific details.
- Every paper `discussion_summary` must explicitly include:
  - biological system/context (species, tissue, disease state, or population if available),
  - study design signal (review, cohort, trial, perturbation model, omics profile, etc.),
  - at least 2 concrete anchors from the source fields (example: molecule/pathway names, intervention, endpoint, sample size, modality, timepoint),
  - what is newly learned versus what remains uncertain.
- If key details are missing in metadata/abstract, state exactly what is missing instead of filling with generic prose.

## Narrative template (paper-level)
1. Background (2-4 sentences):
   - Define the specific biological or clinical problem for that paper.
   - Use paper-specific nouns (pathways, disease names, assay modalities), not generic muscle placeholders.
2. Evidence and methods (3-6 sentences):
   - Describe the actual design and evidence source in concrete terms.
   - Name the principal measurements/analyses and the direction of key reported effects where available.
3. Contribution and limits (2-4 sentences):
   - State what this paper changes in current understanding.
   - State caveats bounded to available evidence.
4. Broader implication (1-2 sentences):
   - Close with a concise, higher-level interpretation for muscle biology/translation.

## Narrative template (cluster-level chapter summaries)
- Synthesize cross-paper patterns with explicit references to representative mechanisms, models, and evidence modalities in that cluster.
- Do not list papers mechanically; build a coherent chapter arc:
  - background state of the field,
  - what this week's papers collectively clarify,
  - where evidence converges vs diverges,
  - final broad implication paragraph (short, high-level).

## Required workflow
1. Find latest digest JSON with:
   - `python skills/muscle-digest-enricher/scripts/locate_latest_digest.py`
2. Read JSON and rewrite every cluster chapter summary:
   - example-anchored chapter style (~300 words, not a hard sentence rule)
   - specificity-rich synthesis -> integration of new findings -> concise broad implications
3. Rewrite every paper `discussion_summary`:
   - example-anchored chapter style (~300 words, not a hard sentence rule)
   - background -> methods/evidence -> specific contribution -> concise broad implications
4. Ensure DOI-first links:
   - If `doi` exists, `doi_url` must be `https://doi.org/<doi>`.
5. Run validator:
   - `python skills/muscle-digest-enricher/scripts/validate_digest_enrichment.py <path-to-json>`
6. If validation fails, fix and rerun validator.

## Guardrails
- Do not invent experiments or conclusions absent from the paper data.
- If abstract is missing, state uncertainty explicitly.
- Do not remove existing fields from JSON.
- Prefer concrete nouns and measured outcomes over abstract framing language.
