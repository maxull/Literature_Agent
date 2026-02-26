# Codex Agent Guidelines: Weekly Skeletal Muscle Literature Scout

## Mission
Each week, automatically identify new and relevant literature (peer-reviewed + preprints) related to skeletal muscle homeostasis, maintenance, adaptation, and disease, spanning fundamental mechanistic through translational research.

Produce a Markdown digest that:
1. states what each paper found (key results, methods, evidence),
2. places it in contemporary context (what was known, how this updates it),
3. highlights novel added value (what is genuinely new),
4. captures mechanistic/omic insights without over-focusing on omics,
5. includes an itinerary (table of contents), then per-paper summaries, then full titles/author lists/abstracts.

## Operating Principles (Non-Negotiable)
- No hallucinations: only claim what is supported by paper metadata/abstract/full text (if accessible).
- Contextualization must be bounded and explicit when uncertain.
- Traceability: every paper entry includes persistent identifier/link and source.
- Relevance-first: prioritize skeletal muscle biology.
- Weekly delta: maintain a seen registry and avoid re-summarizing already covered papers.

## Sources to Search (Minimum)
- Peer-reviewed: PubMed (or Europe PMC), optional Crossref/Semantic Scholar.
- Preprints: bioRxiv, medRxiv, sportRxiv, optional arXiv.

## Relevance and Prioritization
Two-stage pipeline:
1. Fast inclusion/exclusion rules for direct skeletal muscle relevance.
2. Ranking by mechanistic depth, novelty, translational relevance, technical innovation, and evidence clarity.

Target output size: 10-25 papers/week (configurable).

## Output Requirements
One file per run:
- `weekly_muscle_digest_YYYY-MM-DD.md`

Required order:
1. `# Weekly Skeletal Muscle Literature Digest (YYYY-MM-DD)`
2. `## Coverage`
3. `## Highlights (Top 3-5)`
4. `## Paper Summaries`
5. `## Abstracts (Full)`

Include an itinerary near the top with anchor links to highlights, each paper section, and abstracts.

## State and Logging
Maintain:
- `state_seen.json`
- `run_log.json`

Deduplicate by: DOI > PMID > preprint DOI/arXiv ID; keep newest version and note version when available.

## Error Handling
If sources/abstract retrieval fail, continue producing report with explicit source issue notes and conservative interpretation.

## Quality Controls
Before finalizing a report, verify every summary has:
- identifier/link,
- "What's new" section,
- caveats section,
- abstract included or marked unavailable,
- no duplicate entries.

## Scheduling
Run weekly (e.g., Mondays), default date window = last 7 days.

## Config Knobs (`config.yaml`)
- `days_back`
- `max_candidates_per_source`
- `max_summaries_total`
- `include_keywords` / `exclude_keywords`
- `preferred_topics`
- `include_reviews`

## Summarization Constraints
- Use structured output matching the template.
- Avoid marketing language.
- Avoid claiming causality without causal experiments.
- Classify evidence where relevant: correlative, associative, causal, computational, observational.
