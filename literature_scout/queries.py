from __future__ import annotations

from hashlib import sha256

BASE_THEME_GROUPS: dict[str, list[str]] = {
    "muscle_core": [
        "skeletal muscle",
        "myofiber",
        "myonuclei",
        "satellite cell",
        "myogenesis",
        "muscle regeneration",
    ],
    "adaptation": [
        "hypertrophy",
        "atrophy",
        "unloading",
        "exercise adaptation",
        "endurance training",
        "resistance training",
    ],
    "cellular_homeostasis": [
        "proteostasis",
        "autophagy",
        "ubiquitin proteasome",
        "mitochondria",
        "ER stress",
        "oxidative stress",
    ],
    "metabolism": [
        "insulin sensitivity",
        "lipid handling",
        "glycogen",
        "NAD+",
        "sirtuin",
    ],
    "immune_and_matrix": [
        "inflammation",
        "macrophage",
        "myokine",
        "extracellular matrix",
        "fibrosis",
        "angiogenesis",
    ],
    "neuromuscular": [
        "neuromuscular junction",
        "motor neuron",
    ],
    "disease": [
        "aging",
        "sarcopenia",
        "cachexia",
        "muscular dystrophy",
        "myopathy",
        "type 2 diabetes",
        "obesity",
    ],
    "crosstalk": [
        "muscle adipose",
        "muscle liver",
        "muscle bone",
        "gut muscle",
        "brain muscle",
    ],
    "omics": [
        "single-cell RNA",
        "snRNA",
        "scATAC",
        "spatial transcriptomics",
        "proteomics",
        "phosphoproteomics",
        "metabolomics",
        "epigenomics",
        "CRISPR screen",
    ],
}


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(normalized)
    return ordered


def build_pubmed_query(
    extra_keywords: list[str] | None = None,
    journal_filters: list[str] | None = None,
) -> str:
    terms: list[str] = [term for group in BASE_THEME_GROUPS.values() for term in group]
    if extra_keywords:
        terms.extend(extra_keywords)
    terms = _dedupe_keep_order(terms)

    theme_clause = "(" + " OR ".join(f'"{term}"[Title/Abstract]' for term in terms) + ")"

    if not journal_filters:
        return theme_clause

    journals = _dedupe_keep_order(journal_filters)
    journal_clause = "(" + " OR ".join(f'"{journal}"[Journal]' for journal in journals) + ")"
    return f"{theme_clause} AND {journal_clause}"


def build_keyword_query(extra_keywords: list[str] | None = None) -> str:
    terms: list[str] = [term for group in BASE_THEME_GROUPS.values() for term in group]
    if extra_keywords:
        terms.extend(extra_keywords)
    return " OR ".join(_dedupe_keep_order(terms))


def query_set_hash(
    extra_keywords: list[str] | None = None,
    journal_tiers: dict[str, list[str]] | None = None,
    active_tiers: list[str] | None = None,
) -> str:
    parts: list[str] = [build_keyword_query(extra_keywords)]
    if journal_tiers:
        tiers = active_tiers or sorted(journal_tiers)
        for tier in tiers:
            journals = journal_tiers.get(tier, [])
            parts.append(f"{tier}:{'|'.join(_dedupe_keep_order(journals))}")
    joined = "\n".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()
