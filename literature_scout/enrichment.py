from __future__ import annotations

import re

from .models import Paper


CLUSTER_RULES: dict[str, list[str]] = {
    "Regeneration and Stem Cell Dynamics": [
        "satellite cell",
        "myogenesis",
        "regeneration",
        "stem cell",
        "lineage",
        "myonuclei",
    ],
    "Mechanistic Signaling and Proteostasis": [
        "autophagy",
        "proteostasis",
        "ubiquitin",
        "mitochondria",
        "er stress",
        "oxidative stress",
        "pathway",
        "knockout",
        "crispr",
    ],
    "Disease, Aging, and Clinical Translation": [
        "sarcopenia",
        "cachexia",
        "muscular dystrophy",
        "myopathy",
        "aging",
        "patient",
        "clinical",
        "biomarker",
        "therapy",
    ],
    "Metabolism, Endocrinology, and Insulin Action": [
        "insulin",
        "glucose",
        "metabolism",
        "lipid",
        "glycogen",
        "sirtuin",
        "nad",
        "diabetes",
        "obesity",
    ],
    "Inflammation and Cross-Tissue Crosstalk": [
        "macrophage",
        "immune",
        "inflammation",
        "cytokine",
        "myokine",
        "adipose",
        "liver",
        "gut",
        "brain",
    ],
    "ECM, Vascular, and Tissue Remodeling": [
        "extracellular matrix",
        "fibrosis",
        "angiogenesis",
        "vascular",
        "matrix",
        "mechanobiology",
    ],
    "Omics and Systems Biology": [
        "single-cell",
        "scrna",
        "snrna",
        "scatac",
        "spatial",
        "proteomics",
        "phosphoproteomics",
        "metabolomics",
        "epigenomics",
        "multi-omics",
    ],
}

METHOD_ALIASES: dict[str, list[str]] = {
    "Transcriptomics": ["transcriptomics", "rna-seq", "bulk rna", "gene expression profiling"],
    "Single-cell RNA-seq": ["scrna", "single-cell rna", "single cell rna", "scrna-seq", "single-cell"],
    "snRNA-seq": ["snrna", "single-nucleus", "single nucleus rna", "snrna-seq"],
    "Spatial Transcriptomics": ["spatial transcriptomics", "spatial rna", "visium"],
    "Proteomics": ["proteomics", "mass spectrometry proteomics"],
    "Spatial Proteomics": ["spatial proteomics", "imaging mass cytometry", "multiplex protein imaging"],
    "Phosphoproteomics": ["phosphoproteomics", "phospho-proteomics"],
    "Metabolomics": ["metabolomics", "metabolic profiling"],
    "Epigenomics": ["epigenomics", "chromatin", "histone", "dna methylation"],
    "ATAC-seq": ["atac-seq", "atac", "chromatin accessibility"],
    "scATAC-seq": ["scatac", "single-cell atac", "single cell atac"],
    "CRISPR Screen": ["crispr screen", "crisper screen", "pooled crispr"],
    "Lineage Tracing": ["lineage tracing", "fate mapping", "lineage map"],
    "Insulin Sensitivity": [
        "insulin sensitivity",
        "hyperinsulinemic-euglycemic clamp",
        "euglycemic clamp",
        "insulin clamp",
        "homa-ir",
    ],
    "Glucose Tolerance": ["glucose tolerance test", "ogtt", "ipgtt"],
    "Exercise Physiology": ["exercise training", "endurance", "resistance training", "unloading"],
}


def _normalize(text: str) -> str:
    lowered = text.lower().replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9+\-\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def assign_cluster(paper: Paper) -> str:
    text = _normalize(f"{paper.title} {paper.abstract} {paper.venue}")
    best_cluster = "Skeletal Muscle Homeostasis and Adaptation"
    best_score = 0

    for cluster, keywords in CLUSTER_RULES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_cluster = cluster
            best_score = score

    return best_cluster


def extract_methods_keywords(paper: Paper, configured_keywords: list[str]) -> list[str]:
    text = _normalize(f"{paper.title} {paper.abstract}")
    methods: list[str] = []

    for canonical, aliases in METHOD_ALIASES.items():
        if any(_normalize(alias) in text for alias in aliases):
            methods.append(canonical)

    for configured in configured_keywords:
        normalized = _normalize(configured)
        if normalized and normalized in text and configured not in methods:
            methods.append(configured)

    return methods


def get_key_visual_link(paper: Paper) -> tuple[str, str]:
    if paper.url:
        return (
            "Source page (often includes graphical abstract / key figures)",
            paper.url,
        )
    if paper.doi:
        return ("Publisher page (check graphical abstract/figures)", f"https://doi.org/{paper.doi}")
    if paper.pmid:
        return ("PubMed record (figure links when available)", f"https://pubmed.ncbi.nlm.nih.gov/{paper.pmid}/")
    return ("Key visual unavailable from metadata", "")
