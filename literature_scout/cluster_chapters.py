from __future__ import annotations

from collections import Counter, defaultdict

from .config import ScoutConfig
from .llm_client import llm_ready, summarize_cluster_with_llm
from .models import PaperSummary


CLUSTER_BACKGROUND: dict[str, str] = {
    "Regeneration and Stem Cell Dynamics": (
        "Skeletal muscle regeneration is coordinated by satellite cell activation, lineage commitment, "
        "and interactions with immune and stromal niche signals."
    ),
    "Mechanistic Signaling and Proteostasis": (
        "Skeletal muscle homeostasis depends on integrated signaling networks that control proteostasis, "
        "mitochondrial function, and stress adaptation under physiological load."
    ),
    "Disease, Aging, and Clinical Translation": (
        "Muscle disease biology integrates age-dependent decline, systemic metabolic stress, and tissue-specific "
        "degenerative programs that influence function and therapy response."
    ),
    "Metabolism, Endocrinology, and Insulin Action": (
        "Skeletal muscle is a major metabolic organ that regulates whole-body glucose and lipid flux through "
        "insulin-sensitive transport, substrate selection, and mitochondrial remodeling."
    ),
    "Inflammation and Cross-Tissue Crosstalk": (
        "Muscle adaptation is shaped by bidirectional signaling between immune, adipose, liver, gut, and neural axes, "
        "which can amplify repair or drive chronic dysfunction."
    ),
    "ECM, Vascular, and Tissue Remodeling": (
        "Extracellular matrix architecture and vascular remodeling set mechanical and trophic constraints on muscle "
        "plasticity, regeneration, and fibrosis trajectories."
    ),
    "Omics and Systems Biology": (
        "High-dimensional profiling methods are redefining muscle biology by resolving cell states, spatial organization, "
        "and multi-layer regulatory programs across adaptation and disease."
    ),
    "Skeletal Muscle Homeostasis and Adaptation": (
        "Skeletal muscle biology integrates molecular regulation, tissue organization, and systemic physiology to "
        "maintain contractile function across stress states."
    ),
}


def _heuristic_cluster_chapter(cluster: str, papers: list[PaperSummary]) -> str:
    base = CLUSTER_BACKGROUND.get(cluster, CLUSTER_BACKGROUND["Skeletal Muscle Homeostasis and Adaptation"])
    evidence_counter = Counter(item.evidence_class for item in papers if item.evidence_class)
    method_counter = Counter(
        keyword
        for item in papers
        for keyword in item.methods_keywords
    )

    top_evidence = ", ".join(label for label, _ in evidence_counter.most_common(3)) or "mixed evidence"
    top_methods = ", ".join(label for label, _ in method_counter.most_common(4)) or "multi-model approaches"

    sentence_2 = (
        "Historically, unresolved questions in this area have centered on which pathways are causal drivers versus "
        "context-dependent correlates across species, loading states, and disease settings."
    )
    sentence_3 = (
        f"In this update, {len(papers)} new papers converge on this cluster using {top_methods}, "
        f"with the current evidence profile dominated by {top_evidence}."
    )
    sentence_4 = (
        "Collectively, these studies refine mechanistic priors and clarify which molecular modules appear robust enough "
        "to prioritize for perturbation-based follow-up."
    )
    sentence_5 = (
        "The translational implication is that pathway-level interpretation is becoming more precise, but model "
        "heterogeneity and endpoint consistency remain limiting factors for cross-study synthesis."
    )
    return " ".join([base, sentence_2, sentence_3, sentence_4, sentence_5])


def build_cluster_chapters(
    summaries: list[PaperSummary],
    config: ScoutConfig,
    warnings: list[str] | None = None,
) -> dict[str, str]:
    grouped: dict[str, list[PaperSummary]] = defaultdict(list)
    for summary in summaries:
        grouped[summary.cluster].append(summary)

    chapters: dict[str, str] = {}
    for cluster, items in grouped.items():
        chapter_text = None
        if llm_ready(config):
            try:
                chapter_text = summarize_cluster_with_llm(cluster=cluster, items=items, config=config)
            except Exception as exc:  # noqa: BLE001
                if warnings is not None:
                    warnings.append(f"LLM cluster summary fallback for '{cluster}': {exc}")

        if not chapter_text:
            chapter_text = _heuristic_cluster_chapter(cluster, items)

        chapters[cluster] = chapter_text

    return chapters
