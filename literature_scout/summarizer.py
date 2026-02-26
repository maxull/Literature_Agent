from __future__ import annotations

import re
from typing import Iterable

from .models import Paper, PaperSummary, RankedPaper


def _sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _truncate(text: str, max_len: int = 95) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def _evidence_class(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("knockout", "crisper", "crispr", "lineage tracing", "ablation")):
        return "causal"
    if any(term in lowered for term in ("single-cell", "proteomics", "metabolomics", "atac", "spatial")):
        return "computational + experimental"
    if any(term in lowered for term in ("association", "cohort", "observational", "correl")):
        return "observational/associative"
    return "experimental (causality not explicit in abstract)"


def _first_or_default(items: Iterable[str], default: str) -> str:
    for item in items:
        if item:
            return item
    return default


def summarize_ranked_papers(ranked: list[RankedPaper]) -> list[PaperSummary]:
    summaries: list[PaperSummary] = []

    for ranked_item in ranked:
        paper = ranked_item.paper
        abstract = paper.abstract.strip()
        sentence_list = _sentences(abstract)
        has_full_abstract = bool(abstract)

        default_core = (
            "The study investigates mechanisms relevant to skeletal muscle regulation in the reported model."
        )
        core_question = _first_or_default(sentence_list[:1], default_core)

        findings: list[str] = []
        for sentence in sentence_list[:5]:
            findings.append(f"{sentence} [evidence class: {_evidence_class(sentence)}]")
        if not findings:
            findings.append("Abstract unavailable; findings cannot be extracted without full text/metadata.")

        mechanism: list[str] = []
        mechanism_cues = [
            sentence
            for sentence in sentence_list
            if any(token in sentence.lower() for token in ("via", "through", "regulates", "mediates", "pathway"))
        ]
        if mechanism_cues:
            mechanism.append(f"Supported by reported data: {mechanism_cues[0]}")
            if len(mechanism_cues) > 1:
                mechanism.append(f"Proposed/speculative extension: {mechanism_cues[1]}")
        else:
            mechanism.append(
                "Proposed/speculative: abstract does not explicitly define a full causal pathway; full text review needed."
            )

        known_before = [
            "Prior literature has suggested skeletal muscle adaptation and pathology are shaped by cell-intrinsic and niche signals.",
            "Before this study, details of the implicated pathway/cell-state linkage were likely incomplete or context-dependent.",
        ]
        if not has_full_abstract:
            known_before.append(
                "Context statement is conservative because an abstract was not available from the source payload."
            )

        novel_value = [
            "Adds value by contributing a new data point on skeletal muscle regulation in this model/system.",
            f"Provides updated evidence class ({_evidence_class(abstract)}) for this topic area.",
        ]
        if any(term in abstract.lower() for term in ("single-cell", "spatial", "proteomics", "metabolomics")):
            novel_value.append("Adds multi-omic/cell-state resolution that can refine mechanistic hypotheses.")

        implications = [
            "Refines current models of muscle homeostasis/adaptation under physiological or disease stress.",
            "May inform target prioritization or biomarker hypotheses where translational endpoints are reported.",
        ]

        caveats = [
            "Interpretation is limited to source metadata/abstract; causal strength should be verified in full text.",
            "Generalizability across species, sex, age, and training/disease contexts remains to be tested.",
            "High-value follow-up: perturb the highlighted node/pathway longitudinally and quantify functional muscle outcomes.",
        ]

        relevance = (
            "This study is relevant to skeletal muscle regulation through within-cell control (e.g., proteostasis/metabolism), "
            "cellular cross-talk within muscle niches, and/or broader inter-organ signaling in health or disease contexts."
        )

        summaries.append(
            PaperSummary(
                paper=paper,
                short_title=_truncate(paper.title, max_len=90),
                core_question=core_question,
                key_findings=findings,
                mechanism=mechanism,
                known_before=known_before,
                novel_value=novel_value,
                implications=implications,
                caveats=caveats,
                relevance=relevance,
                evidence_class=_evidence_class(abstract),
            )
        )

    return summaries
