from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


DEFAULT_JOURNAL_TIERS: dict[str, list[str]] = {
    "tier_1": [
        "Skeletal Muscle",
        "Journal of Physiology",
        "Journal of Applied Physiology",
        "American Journal of Physiology-Cell Physiology",
        "American Journal of Physiology-Endocrinology and Metabolism",
        "Journal of Cachexia, Sarcopenia and Muscle",
        "Cell Metabolism",
        "Nature Metabolism",
        "Journal of Clinical Investigation",
        "Diabetes",
        "Diabetologia",
        "Developmental Cell",
        "Cell Stem Cell",
        "Nature Cell Biology",
        "Nature Communications",
        "Science Advances",
        "Proceedings of the National Academy of Sciences of the United States of America",
        "Autophagy",
        "Aging Cell",
        "Matrix Biology",
    ],
    "tier_2": [
        "Cell",
        "Nature",
        "Science",
        "Nature Medicine",
        "Nature Aging",
        "Nature Genetics",
        "Molecular Cell",
        "Genes & Development",
        "Immunity",
        "Nature Immunology",
        "Journal of Experimental Medicine",
        "Science Immunology",
        "Nature Biotechnology",
        "Nature Methods",
        "Genome Biology",
        "Genome Research",
        "Cell Systems",
        "Nucleic Acids Research",
        "Redox Biology",
        "Cell Death and Differentiation",
    ],
    "tier_3": [
        "Medicine and Science in Sports and Exercise",
        "European Journal of Applied Physiology",
        "Physiological Reports",
        "Frontiers in Physiology",
        "Muscle & Nerve",
        "Neuromuscular Disorders",
        "Acta Physiologica",
        "Experimental Physiology",
        "Stem Cell Reports",
        "EMBO Journal",
        "EMBO Reports",
        "Journal of Cell Biology",
        "Cell Reports",
        "eLife",
        "Endocrinology",
        "Journal of Endocrinology",
        "Metabolism",
        "GeroScience",
        "Free Radical Biology & Medicine",
        "Mitochondrion",
        "Clinical Science",
        "Clinical Nutrition",
        "British Journal of Sports Medicine",
        "JAMA Network Open",
        "Orphanet Journal of Rare Diseases",
    ],
}

DEFAULT_JOURNAL_TIER_WEIGHTS: dict[str, float] = {
    "tier_1": 3.2,
    "tier_2": 1.8,
    "tier_3": 0.9,
}

DEFAULT_METHOD_KEYWORDS: list[str] = [
    "transcriptomics",
    "single-cell RNA-seq",
    "snRNA-seq",
    "spatial transcriptomics",
    "proteomics",
    "spatial proteomics",
    "phosphoproteomics",
    "metabolomics",
    "epigenomics",
    "ATAC-seq",
    "scATAC-seq",
    "CRISPR screens",
    "lineage tracing",
    "insulin sensitivity",
    "hyperinsulinemic-euglycemic clamp",
    "glucose tolerance test",
    "mitochondrial respiration",
]


@dataclass
class ScoutConfig:
    days_back: int
    max_candidates_per_source: int
    max_summaries_total: int
    include_keywords: list[str]
    exclude_keywords: list[str]
    preferred_topics: list[str]
    methods_keywords: list[str]
    include_reviews: bool
    include_arxiv: bool
    include_general_pubmed: bool
    exhaustive_output: bool
    other_potential_limit: int
    journal_tiers: dict[str, list[str]]
    active_journal_tiers: list[str]
    journal_tier_weights: dict[str, float]
    use_llm_summaries: bool
    llm_model: str
    llm_api_base: str
    llm_temperature: float
    llm_timeout_seconds: int
    output_dir: Path
    state_seen_file: Path
    run_log_file: Path
    request_timeout_seconds: int
    retry_attempts: int


def _copy_tiers(source: dict[str, list[str]]) -> dict[str, list[str]]:
    return {tier: list(journals) for tier, journals in source.items()}


def _copy_weights(source: dict[str, float]) -> dict[str, float]:
    return {tier: float(weight) for tier, weight in source.items()}


DEFAULT_CONFIG = ScoutConfig(
    days_back=7,
    max_candidates_per_source=240,
    max_summaries_total=80,
    include_keywords=[],
    exclude_keywords=[],
    preferred_topics=[],
    methods_keywords=list(DEFAULT_METHOD_KEYWORDS),
    include_reviews=True,
    include_arxiv=False,
    include_general_pubmed=True,
    exhaustive_output=True,
    other_potential_limit=250,
    journal_tiers=_copy_tiers(DEFAULT_JOURNAL_TIERS),
    active_journal_tiers=["tier_1", "tier_2", "tier_3"],
    journal_tier_weights=_copy_weights(DEFAULT_JOURNAL_TIER_WEIGHTS),
    use_llm_summaries=True,
    llm_model="gpt-4o-mini",
    llm_api_base="https://api.openai.com/v1",
    llm_temperature=0.2,
    llm_timeout_seconds=45,
    output_dir=Path("reports/weekly_digests"),
    state_seen_file=Path("state_seen.json"),
    run_log_file=Path("run_log.json"),
    request_timeout_seconds=25,
    retry_attempts=3,
)


def load_config(config_path: str | Path = "config.yaml") -> ScoutConfig:
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_CONFIG

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    raw_tiers = raw.get("journal_tiers", DEFAULT_JOURNAL_TIERS)
    journal_tiers = {
        str(tier): [str(journal) for journal in (journals or [])]
        for tier, journals in raw_tiers.items()
    }

    raw_weights = raw.get("journal_tier_weights", DEFAULT_JOURNAL_TIER_WEIGHTS)
    journal_tier_weights = {str(tier): float(weight) for tier, weight in raw_weights.items()}

    return ScoutConfig(
        days_back=int(raw.get("days_back", DEFAULT_CONFIG.days_back)),
        max_candidates_per_source=int(
            raw.get("max_candidates_per_source", DEFAULT_CONFIG.max_candidates_per_source)
        ),
        max_summaries_total=int(raw.get("max_summaries_total", DEFAULT_CONFIG.max_summaries_total)),
        include_keywords=list(raw.get("include_keywords", DEFAULT_CONFIG.include_keywords)),
        exclude_keywords=list(raw.get("exclude_keywords", DEFAULT_CONFIG.exclude_keywords)),
        preferred_topics=list(raw.get("preferred_topics", DEFAULT_CONFIG.preferred_topics)),
        methods_keywords=list(raw.get("methods_keywords", DEFAULT_CONFIG.methods_keywords)),
        include_reviews=bool(raw.get("include_reviews", DEFAULT_CONFIG.include_reviews)),
        include_arxiv=bool(raw.get("include_arxiv", DEFAULT_CONFIG.include_arxiv)),
        include_general_pubmed=bool(
            raw.get("include_general_pubmed", DEFAULT_CONFIG.include_general_pubmed)
        ),
        exhaustive_output=bool(raw.get("exhaustive_output", DEFAULT_CONFIG.exhaustive_output)),
        other_potential_limit=int(
            raw.get("other_potential_limit", DEFAULT_CONFIG.other_potential_limit)
        ),
        journal_tiers=journal_tiers,
        active_journal_tiers=list(raw.get("active_journal_tiers", DEFAULT_CONFIG.active_journal_tiers)),
        journal_tier_weights=journal_tier_weights,
        use_llm_summaries=bool(raw.get("use_llm_summaries", DEFAULT_CONFIG.use_llm_summaries)),
        llm_model=str(raw.get("llm_model", DEFAULT_CONFIG.llm_model)),
        llm_api_base=str(raw.get("llm_api_base", DEFAULT_CONFIG.llm_api_base)),
        llm_temperature=float(raw.get("llm_temperature", DEFAULT_CONFIG.llm_temperature)),
        llm_timeout_seconds=int(raw.get("llm_timeout_seconds", DEFAULT_CONFIG.llm_timeout_seconds)),
        output_dir=Path(raw.get("output_dir", str(DEFAULT_CONFIG.output_dir))),
        state_seen_file=Path(raw.get("state_seen_file", str(DEFAULT_CONFIG.state_seen_file))),
        run_log_file=Path(raw.get("run_log_file", str(DEFAULT_CONFIG.run_log_file))),
        request_timeout_seconds=int(
            raw.get("request_timeout_seconds", DEFAULT_CONFIG.request_timeout_seconds)
        ),
        retry_attempts=int(raw.get("retry_attempts", DEFAULT_CONFIG.retry_attempts)),
    )
