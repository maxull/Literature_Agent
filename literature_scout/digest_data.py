from __future__ import annotations

from collections import defaultdict
from datetime import date

from .models import PaperSummary, RankedPaper


def _doi_url(summary: PaperSummary) -> str:
    paper = summary.paper
    if paper.doi:
        return f"https://doi.org/{paper.doi}"
    return ""


def _paper_record(summary: PaperSummary, is_highlight: bool) -> dict:
    paper = summary.paper
    doi_url = _doi_url(summary)
    return {
        "identifier": paper.identifier,
        "title": paper.title,
        "short_title": summary.short_title,
        "authors": paper.authors,
        "venue": paper.venue,
        "year": paper.year,
        "published_date": paper.published_date.isoformat(),
        "source": paper.source,
        "source_type": paper.source_type,
        "study_type": paper.study_type,
        "tags": paper.tags,
        "methods_keywords": summary.methods_keywords,
        "cluster": summary.cluster,
        "evidence_class": summary.evidence_class,
        "core_question": summary.core_question,
        "discussion_summary": summary.discussion_summary,
        "key_findings": " ".join(summary.key_findings),
        "mechanism": " ".join(summary.mechanism),
        "known_before": " ".join(summary.known_before),
        "novel_value": " ".join(summary.novel_value),
        "implications": " ".join(summary.implications),
        "caveats": " ".join(summary.caveats),
        "relevance": summary.relevance,
        "abstract": paper.abstract or "Abstract unavailable.",
        "doi": paper.doi or "",
        "doi_url": doi_url,
        "fallback_url": paper.url or paper.citation_link,
        "key_visual_label": summary.key_visual_label,
        "key_visual_link": summary.key_visual_link,
        "is_highlight": is_highlight,
    }


def build_digest_payload(
    run_date: date,
    start_date: date,
    end_date: date,
    source_names: list[str],
    counts_by_source: dict[str, int],
    included_count: int,
    candidate_count: int,
    summaries: list[PaperSummary],
    other_ranked: list[RankedPaper],
    failures: list[str],
    cluster_chapters: dict[str, str],
    search_terms: list[str],
    active_journal_tiers: list[str],
) -> dict:
    highlight_ids = {summary.paper.identifier for summary in summaries[:5]}

    papers: list[dict] = []
    cluster_map: dict[str, list[dict]] = defaultdict(list)
    method_index: dict[str, list[dict]] = defaultdict(list)

    for summary in summaries:
        is_highlight = summary.paper.identifier in highlight_ids
        record = _paper_record(summary, is_highlight=is_highlight)
        papers.append(record)
        cluster_map[summary.cluster].append(record)

        for keyword in summary.methods_keywords:
            method_index[keyword].append(
                {
                    "identifier": summary.paper.identifier,
                    "title": summary.paper.title,
                    "short_title": summary.short_title,
                    "cluster": summary.cluster,
                    "doi": summary.paper.doi or "",
                    "doi_url": _doi_url(summary),
                }
            )

    for cluster_name, items in cluster_map.items():
        items.sort(key=lambda item: (item["is_highlight"], item["year"]), reverse=True)

    other_records: list[dict] = []
    for ranked in other_ranked:
        paper = ranked.paper
        other_records.append(
            {
                "identifier": paper.identifier,
                "title": paper.title,
                "doi": paper.doi or "",
                "doi_url": f"https://doi.org/{paper.doi}" if paper.doi else "",
                "fallback_url": paper.url or paper.citation_link,
                "reasons": ranked.reasons,
                "score": ranked.score,
            }
        )

    return {
        "run_date": run_date.isoformat(),
        "coverage": {
            "window_start": start_date.isoformat(),
            "window_end": end_date.isoformat(),
            "sources_searched": source_names,
            "counts_by_source": counts_by_source,
            "candidate_count": candidate_count,
            "included_count": included_count,
            "summarized_count": len(summaries),
            "excluded_after_relevance": max(0, candidate_count - included_count),
            "not_summarized_after_ranking": max(0, included_count - len(summaries)),
            "failures": failures,
        },
        "search_terms": sorted(set(search_terms)),
        "active_journal_tiers": active_journal_tiers,
        "clusters": {
            cluster_name: {
                "chapter_summary": cluster_chapters.get(cluster_name, "Summary unavailable."),
                "papers": items,
            }
            for cluster_name, items in sorted(cluster_map.items())
        },
        "highlights": [record for record in papers if record["is_highlight"]],
        "methods_index": {
            key: sorted(values, key=lambda item: item["short_title"].lower())
            for key, values in sorted(method_index.items(), key=lambda item: item[0].lower())
        },
        "papers": papers,
        "other_potentially_relevant": other_records,
    }
