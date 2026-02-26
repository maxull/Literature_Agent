from __future__ import annotations

import re
from typing import Iterable

from .config import ScoutConfig
from .enrichment import assign_cluster, extract_methods_keywords, get_key_visual_link
from .llm_client import llm_ready, summarize_with_llm
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
        return "computational"
    if any(term in lowered for term in ("association", "cohort", "observational", "correl")):
        return "associative"
    return "mixed"


def _first_or_default(items: Iterable[str], default: str) -> str:
    for item in items:
        if item:
            return item
    return default


def _as_list_field(value: str, fallback: str) -> list[str]:
    cleaned = (value or "").strip()
    return [cleaned if cleaned else fallback]


def _heuristic_summary(
    paper: Paper,
    ranked_item: RankedPaper,
    cluster: str,
    methods_keywords: list[str],
    visual_label: str,
    visual_link: str,
) -> PaperSummary:
    abstract = paper.abstract.strip()
    sentence_list = _sentences(abstract)
    has_full_abstract = bool(abstract)

    core_question = _first_or_default(
        sentence_list[:1],
        "The study investigates mechanisms relevant to skeletal muscle regulation in the reported model.",
    )

    findings_text = " ".join(sentence_list[:4])
    if not findings_text:
        findings_text = "Abstract unavailable; findings cannot be extracted without full text or richer metadata."

    mechanism_cues = [
        sentence
        for sentence in sentence_list
        if any(token in sentence.lower() for token in ("via", "through", "regulates", "mediates", "pathway"))
    ]
    if mechanism_cues:
        mechanism_text = (
            f"Supported by reported data: {mechanism_cues[0]} "
            "Potential extension remains speculative where direct perturbation evidence is not explicit in the abstract."
        )
    else:
        mechanism_text = (
            "The abstract does not provide a complete causal chain, so mechanistic interpretation remains tentative "
            "pending full-text evaluation."
        )

    known_before_text = (
        "Prior literature has suggested that skeletal muscle adaptation and pathology are shaped by interactions between "
        "cell-intrinsic programs and tissue microenvironment signals."
    )
    if not has_full_abstract:
        known_before_text += " This context statement is conservative because abstract detail was unavailable."

    novel_text = (
        "This work adds new evidence in this theme by refining how the implicated biology is measured or interpreted "
        f"within the '{cluster}' domain."
    )

    implications_text = (
        "The results sharpen current models of skeletal muscle regulation and may help prioritize translational hypotheses "
        "when combined with orthogonal perturbation or longitudinal validation studies."
    )

    caveats_text = (
        "Interpretation is currently bounded by metadata and abstract-level detail. Generalizability across species, age, "
        "and disease context remains uncertain. A high-value follow-up is to directly perturb the highlighted node in a "
        "longitudinal design with functional muscle outcomes."
    )

    relevance_text = (
        "This study is relevant to skeletal muscle regulation through within-cell control, cell-to-cell crosstalk within "
        "muscle tissue, and/or broader inter-organ signaling under health or disease stress."
    )
    discussion_text = (
        f"{known_before_text} {novel_text} {implications_text} "
        "Taken together, the study updates current understanding by integrating mechanistic context with the newly reported evidence."
    )

    if ranked_item.reasons:
        implications_text += f" Ranking signals for prioritization: {', '.join(ranked_item.reasons)}."

    return PaperSummary(
        paper=paper,
        short_title=_truncate(paper.title, max_len=90),
        core_question=core_question,
        key_findings=_as_list_field(findings_text, "Findings unavailable."),
        mechanism=_as_list_field(mechanism_text, "Mechanistic interpretation unavailable."),
        known_before=_as_list_field(known_before_text, "Prior context unavailable."),
        novel_value=_as_list_field(novel_text, "Novel value unavailable."),
        implications=_as_list_field(implications_text, "Implications unavailable."),
        caveats=_as_list_field(caveats_text, "Caveats unavailable."),
        relevance=relevance_text,
        evidence_class=_evidence_class(abstract),
        discussion_summary=discussion_text,
        cluster=cluster,
        methods_keywords=methods_keywords,
        key_visual_label=visual_label,
        key_visual_link=visual_link,
    )


def summarize_ranked_papers(
    ranked: list[RankedPaper],
    config: ScoutConfig,
    warnings: list[str] | None = None,
) -> list[PaperSummary]:
    summaries: list[PaperSummary] = []
    use_llm = llm_ready(config)

    for ranked_item in ranked:
        paper = ranked_item.paper
        cluster = assign_cluster(paper)
        methods_keywords = extract_methods_keywords(paper, configured_keywords=config.methods_keywords)
        visual_label, visual_link = get_key_visual_link(paper)

        if use_llm:
            try:
                llm_payload = summarize_with_llm(
                    paper=paper,
                    cluster=cluster,
                    methods_keywords=methods_keywords,
                    ranking_reasons=ranked_item.reasons,
                    config=config,
                )
            except Exception as exc:  # noqa: BLE001
                llm_payload = None
                if warnings is not None:
                    warnings.append(f"LLM summary fallback for '{paper.title}': {exc}")

            if llm_payload:
                evidence_class = str(llm_payload.get("evidence_class", "mixed")).strip() or "mixed"
                discussion_summary = (
                    str(llm_payload.get("discussion_summary", "")).strip()
                    or str(llm_payload.get("novel_value", "")).strip()
                    or "Discussion summary unavailable."
                )
                summaries.append(
                    PaperSummary(
                        paper=paper,
                        short_title=_truncate(
                            str(llm_payload.get("short_title", paper.title)).strip() or paper.title,
                            max_len=90,
                        ),
                        core_question=str(llm_payload.get("core_question", "")).strip()
                        or "Core question could not be resolved from available metadata.",
                        key_findings=_as_list_field(
                            str(llm_payload.get("key_findings", "")).strip(),
                            "Findings unavailable.",
                        ),
                        mechanism=_as_list_field(
                            str(llm_payload.get("mechanism", "")).strip(),
                            "Mechanistic interpretation unavailable.",
                        ),
                        known_before=_as_list_field(
                            str(llm_payload.get("known_before", "")).strip(),
                            "Prior context unavailable.",
                        ),
                        novel_value=_as_list_field(
                            str(llm_payload.get("novel_value", "")).strip(),
                            "Novel value unavailable.",
                        ),
                        implications=_as_list_field(
                            str(llm_payload.get("implications", "")).strip(),
                            "Implications unavailable.",
                        ),
                        caveats=_as_list_field(
                            str(llm_payload.get("caveats", "")).strip(),
                            "Caveats unavailable.",
                        ),
                        relevance=str(llm_payload.get("relevance", "")).strip()
                        or "Relevance to muscle regulation could not be fully established from available metadata.",
                        evidence_class=evidence_class,
                        discussion_summary=discussion_summary,
                        cluster=cluster,
                        methods_keywords=methods_keywords,
                        key_visual_label=str(llm_payload.get("key_visual_label", visual_label)).strip()
                        or visual_label,
                        key_visual_link=visual_link,
                    )
                )
                continue

        summaries.append(
            _heuristic_summary(
                paper=paper,
                ranked_item=ranked_item,
                cluster=cluster,
                methods_keywords=methods_keywords,
                visual_label=visual_label,
                visual_link=visual_link,
            )
        )

    return summaries
