from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from .models import PaperSummary, RankedPaper


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s_]+", "-", cleaned)


def _format_author_short(authors: list[str]) -> str:
    if not authors:
        return "Unknown authors"
    if len(authors) <= 3:
        return ", ".join(authors)
    return ", ".join(authors[:3]) + ", et al."


def _identifier_text(summary: PaperSummary) -> str:
    paper = summary.paper
    version_note = f"; Version {paper.version}" if paper.version else ""
    if paper.doi:
        return f"DOI: {paper.doi}{version_note}"
    if paper.pmid:
        return f"PMID: {paper.pmid}{version_note}"
    if paper.preprint_id:
        return f"Preprint DOI/ID: {paper.preprint_id}{version_note}"
    if paper.arxiv_id:
        return f"arXiv: {paper.arxiv_id}{version_note}"
    return "Identifier unavailable"


def _source_label(source: str) -> str:
    lowered = source.lower()
    if lowered == "biorxiv":
        return "bioRxiv"
    if lowered == "medrxiv":
        return "medRxiv"
    if lowered == "sportrxiv":
        return "sportRxiv"
    return source


def _paragraph(lines: list[str], fallback: str) -> str:
    cleaned = [line.strip() for line in lines if line.strip()]
    return " ".join(cleaned) if cleaned else fallback


def _clustered(summaries: list[PaperSummary]) -> dict[str, list[PaperSummary]]:
    buckets: dict[str, list[PaperSummary]] = defaultdict(list)
    for summary in summaries:
        buckets[summary.cluster].append(summary)

    return dict(sorted(buckets.items(), key=lambda item: len(item[1]), reverse=True))


def _methods_index(summaries: list[PaperSummary]) -> dict[str, list[PaperSummary]]:
    index: dict[str, list[PaperSummary]] = defaultdict(list)
    for summary in summaries:
        for keyword in summary.methods_keywords:
            index[keyword].append(summary)
    return dict(sorted(index.items(), key=lambda item: item[0].lower()))


def _summary_anchor(summary: PaperSummary) -> str:
    return _slugify(f"{summary.short_title} {summary.paper.year} source {summary.paper.source}")


def render_markdown(
    run_date: date,
    start_date: date,
    end_date: date,
    source_names: list[str],
    candidate_count: int,
    summarized: list[PaperSummary],
    other_ranked: list[RankedPaper],
    failures: list[str],
) -> str:
    clustered = _clustered(summarized)
    methods_index = _methods_index(summarized)

    title = f"# Weekly Skeletal Muscle Literature Digest ({run_date.isoformat()})"
    lines: list[str] = [
        title,
        f"Coverage window: papers published/posted from {start_date.isoformat()} to {end_date.isoformat()}.",
        "",
        "## Itinerary",
        "- [Highlights (top 3-5)](#highlights-top-3-5)",
        "- [Thematic Clusters](#thematic-clusters)",
        "- [Methods Keyword Index](#methods-keyword-index)",
    ]

    for cluster_name in clustered:
        lines.append(f"- [Cluster: {cluster_name}](#{_slugify(f'cluster {cluster_name}')})")

    for summary in summarized:
        lines.append(f"- [{summary.short_title}](#{_summary_anchor(summary)})")

    lines.extend(
        [
            "- [Abstracts (full text)](#abstracts-full)",
            "",
            "## Coverage",
            f"- Date window: {start_date.isoformat()} to {end_date.isoformat()}",
            f"- Sources searched: {', '.join(source_names)}",
            f"- Number found (deduplicated candidates): {candidate_count}",
            f"- Number summarized: {len(summarized)}",
        ]
    )

    if failures:
        lines.append(f"- Source issues: {' | '.join(failures)}")

    lines.append("")
    lines.append("## Highlights (Top 3-5)")
    highlight_items = summarized[:5]
    if not highlight_items:
        lines.append("No papers met summary criteria this run.")
    else:
        for summary in highlight_items:
            lines.append(f"### {summary.short_title}")
            highlight_text = (
                f"{_paragraph(summary.novel_value, 'Novelty detail unavailable.')} "
                f"{_paragraph(summary.implications, 'Implications detail unavailable.') }"
            ).strip()
            lines.append(highlight_text)
            study_type = summary.paper.study_type or "unspecified"
            if summary.paper.is_review:
                study_type = "Review"
            lines.append(
                f"Study design: {study_type}. Evidence class: {summary.evidence_class}. Cluster: {summary.cluster}."
            )
            if summary.key_visual_link:
                lines.append(f"Key visual: [{summary.key_visual_label}]({summary.key_visual_link})")
            else:
                lines.append("Key visual: unavailable from source metadata.")
            lines.append("")

    lines.append("## Thematic Clusters")
    if not clustered:
        lines.append("No clusters available because no papers were summarized.")
    else:
        for cluster_name, items in clustered.items():
            lines.append(f"### Cluster: {cluster_name}")
            lines.append(f"Papers in cluster: {len(items)}")
            lines.append("")

    lines.append("## Methods Keyword Index")
    if not methods_index:
        lines.append("No method keywords detected in summarized papers.")
    else:
        for keyword, items in methods_index.items():
            linked = ", ".join(f"[{item.short_title}](#{_summary_anchor(item)})" for item in items)
            lines.append(f"- {keyword}: {linked}")

    lines.append("")
    lines.append("## Paper Summaries")

    for cluster_name, cluster_items in clustered.items():
        lines.append(f"### Cluster: {cluster_name}")
        lines.append("")

        for summary in cluster_items:
            paper = summary.paper
            source_label = _source_label(paper.source)
            lines.append(f"#### {summary.short_title} ({paper.year}) — [Source: {source_label}]")

            citation_link = paper.citation_link or ""
            citation_title = f"[{paper.title}]({citation_link})" if citation_link else paper.title
            lines.append(
                f"Citation: {citation_title}, {_format_author_short(paper.authors)}, {paper.venue}, {paper.year}, {_identifier_text(summary)}"
            )
            tags = ", ".join(paper.tags) if paper.tags else "none"
            methods = ", ".join(summary.methods_keywords) if summary.methods_keywords else "none detected"
            study_type = paper.study_type or "unspecified"
            if paper.is_review:
                study_type = "Review"
            lines.append(f"Tags: {tags}")
            lines.append(f"Methods keywords: {methods}")
            lines.append(f"Study type: {study_type}")
            if summary.key_visual_link:
                lines.append(f"Key visual: [{summary.key_visual_label}]({summary.key_visual_link})")
            else:
                lines.append("Key visual: unavailable from source metadata.")
            lines.append("")

            lines.append("1) Core question")
            lines.append(summary.core_question)
            lines.append("")

            lines.append("2) Key findings (what they showed)")
            lines.append(_paragraph(summary.key_findings, "Findings unavailable."))
            lines.append("")

            lines.append("3) Mechanism / model")
            lines.append(_paragraph(summary.mechanism, "Mechanistic detail unavailable."))
            lines.append("")

            lines.append("4) What was known before (contemporary context)")
            lines.append(_paragraph(summary.known_before, "Context unavailable."))
            lines.append("")

            lines.append("5) What's new here (novel added value)")
            lines.append(_paragraph(summary.novel_value, "Novel value unavailable."))
            lines.append("")

            lines.append("6) Implications (why this matters)")
            lines.append(_paragraph(summary.implications, "Implications unavailable."))
            lines.append("")

            lines.append("7) Caveats / open questions")
            lines.append(_paragraph(summary.caveats, "Caveats unavailable."))
            lines.append("")

            lines.append("8) Relevance to skeletal muscle regulation")
            lines.append(summary.relevance)
            lines.append("")

    if other_ranked:
        lines.append("## Other potentially relevant (not summarized)")
        for item in other_ranked:
            paper = item.paper
            link = paper.citation_link
            title = f"[{paper.title}]({link})" if link else paper.title
            reason = ", ".join(item.reasons) if item.reasons else "topic relevance"
            lines.append(f"- {title} — {reason}")
        lines.append("")

    lines.append("## Abstracts (Full)")
    for summary in summarized:
        paper = summary.paper
        lines.append(f"### Full citation: {paper.title}")
        lines.append(f"- Full Title: {paper.title}")
        if paper.authors:
            lines.append(f"- Authors: {', '.join(paper.authors)}")
        else:
            lines.append("- Authors: author list truncated by source")

        abstract_text = paper.abstract.strip() if paper.abstract.strip() else "Abstract unavailable."
        lines.append(f"- Abstract: {abstract_text}")

        links: list[str] = []
        if paper.doi:
            links.append(f"DOI: https://doi.org/{paper.doi}")
        if paper.pmid:
            links.append(f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{paper.pmid}/")
        if paper.url and (not paper.doi or paper.url != f"https://doi.org/{paper.doi}"):
            links.append(f"Source: {paper.url}")
        if not links:
            links.append("Identifier/link unavailable")
        lines.append(f"- Identifiers/Links: {' | '.join(links)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
