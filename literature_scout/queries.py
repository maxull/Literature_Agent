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


def build_pubmed_query(extra_keywords: list[str] | None = None) -> str:
    groups = list(BASE_THEME_GROUPS.values())
    terms: list[str] = [term for group in groups for term in group]
    if extra_keywords:
        terms.extend(extra_keywords)

    expanded = [f'"{term}"[Title/Abstract]' for term in terms]
    return "(" + " OR ".join(expanded) + ")"


def build_keyword_query(extra_keywords: list[str] | None = None) -> str:
    terms: list[str] = [term for group in BASE_THEME_GROUPS.values() for term in group]
    if extra_keywords:
        terms.extend(extra_keywords)
    return " OR ".join({term for term in terms})


def query_set_hash(extra_keywords: list[str] | None = None) -> str:
    query_text = build_keyword_query(extra_keywords)
    return sha256(query_text.encode("utf-8")).hexdigest()
