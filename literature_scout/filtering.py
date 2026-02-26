from __future__ import annotations

import re

from .config import ScoutConfig
from .models import Paper, RankedPaper

CORE_INCLUDE_TERMS = {
    "skeletal muscle",
    "myofiber",
    "myonuclei",
    "satellite cell",
    "myogenesis",
    "muscle regeneration",
    "neuromuscular junction",
}

CROSS_TISSUE_TERMS = {
    "adipose",
    "liver",
    "gut",
    "brain",
    "bone",
    "immune",
    "macrophage",
    "cytokine",
}

MECHANISTIC_TERMS = {
    "knockout",
    "overexpression",
    "crisper",
    "crispr",
    "ablation",
    "lineage tracing",
    "pharmacologic",
    "inhibitor",
    "activation",
    "causal",
}

TECHNICAL_TERMS = {
    "single-cell",
    "scrna",
    "snrna",
    "spatial",
    "proteomics",
    "phosphoproteomics",
    "metabolomics",
    "epigenomics",
    "multi-omics",
    "crispr screen",
}

TRANSLATIONAL_TERMS = {
    "human",
    "patient",
    "clinical",
    "cohort",
    "therapeutic",
    "biomarker",
}

CORRELATIVE_TERMS = {
    "association",
    "correlate",
    "linked with",
    "observational",
}


def _journal_key(text: str) -> str:
    normalized = text.lower().replace("&", "and")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _journal_tier_for_paper(paper: Paper, config: ScoutConfig) -> str | None:
    venue_key = _journal_key(paper.venue)
    if not venue_key:
        return None

    for tier in config.active_journal_tiers:
        journals = config.journal_tiers.get(tier, [])
        for journal in journals:
            journal_key = _journal_key(journal)
            if not journal_key:
                continue
            if journal_key in venue_key or venue_key in journal_key:
                return tier
    return None


def _normalized_text(paper: Paper) -> str:
    return re.sub(r"\s+", " ", f"{paper.title} {paper.abstract}".lower())


def _detect_study_type(text: str) -> str:
    if "randomized" in text or "clinical trial" in text:
        return "clinical trial"
    if "cohort" in text or "patient" in text or "human" in text:
        return "human cohort"
    if "mouse" in text or "murine" in text:
        return "mouse"
    if "rat" in text:
        return "rat"
    if "in vitro" in text or "cell line" in text or "myotube" in text:
        return "in vitro"
    if "organoid" in text:
        return "organoid"
    if "review" in text:
        return "review"
    return "unspecified"


def _extract_tags(text: str) -> list[str]:
    vocabulary = [
        "satellite cells",
        "regeneration",
        "scRNA-seq",
        "inflammation",
        "aging",
        "cachexia",
        "sarcopenia",
        "mitochondria",
        "autophagy",
        "exercise",
        "neuromuscular junction",
        "fibrosis",
        "insulin sensitivity",
        "proteomics",
        "metabolomics",
    ]
    tags = [tag for tag in vocabulary if tag.lower().replace("-", "") in text.replace("-", "")]
    return tags[:8]


def stage1_relevance_filter(candidates: list[Paper], config: ScoutConfig) -> list[Paper]:
    included: list[Paper] = []

    for paper in candidates:
        text = _normalized_text(paper)
        include_terms = CORE_INCLUDE_TERMS | {term.lower() for term in config.include_keywords}
        has_core = any(term in text for term in include_terms)
        has_cross = any(term in text for term in CROSS_TISSUE_TERMS)
        mentions_muscle = "muscle" in text
        has_mechanistic = any(term in text for term in MECHANISTIC_TERMS)
        has_excluded = any(term.lower() in text for term in config.exclude_keywords)

        include = has_core or (has_cross and mentions_muscle)
        if has_excluded and not has_mechanistic:
            include = False

        if not config.include_reviews and paper.is_review:
            include = False

        if include:
            paper.study_type = _detect_study_type(text)
            paper.tags = _extract_tags(text)
            included.append(paper)

    return included


def rank_papers(candidates: list[Paper], config: ScoutConfig) -> list[RankedPaper]:
    ranked: list[RankedPaper] = []

    for paper in candidates:
        text = _normalized_text(paper)
        score = 0.0
        reasons: list[str] = []

        mech_hits = sum(1 for term in MECHANISTIC_TERMS if term in text)
        if mech_hits:
            score += 2.4 * mech_hits
            reasons.append("mechanistic evidence")

        technical_hits = sum(1 for term in TECHNICAL_TERMS if term in text)
        if technical_hits:
            score += 1.5 * technical_hits
            reasons.append("technical innovation")

        translational_hits = sum(1 for term in TRANSLATIONAL_TERMS if term in text)
        if translational_hits:
            score += 1.8 * translational_hits
            reasons.append("translational relevance")

        correlation_hits = sum(1 for term in CORRELATIVE_TERMS if term in text)
        if correlation_hits and mech_hits == 0:
            score -= 0.7 * correlation_hits

        preferred_hits = sum(1 for term in config.preferred_topics if term.lower() in text)
        if preferred_hits:
            score += 1.1 * preferred_hits
            reasons.append("preferred topic match")

        if paper.source_type == "peer-reviewed":
            score += 0.6

        journal_tier = _journal_tier_for_paper(paper, config)
        if journal_tier:
            tier_weight = config.journal_tier_weights.get(journal_tier, 0.0)
            score += tier_weight
            reasons.append(f"{journal_tier} journal")

        ranked.append(RankedPaper(paper=paper, score=score, reasons=sorted(set(reasons))))

    ranked.sort(key=lambda item: (item.score, item.paper.published_date), reverse=True)
    return ranked


def split_ranked(
    ranked: list[RankedPaper], max_summaries: int
) -> tuple[list[RankedPaper], list[RankedPaper]]:
    primary = ranked[:max_summaries]
    remainder = ranked[max_summaries:]
    return primary, remainder
