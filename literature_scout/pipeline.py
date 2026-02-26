from __future__ import annotations

from datetime import datetime, timedelta

from .config import ScoutConfig
from .filtering import rank_papers, split_ranked, stage1_relevance_filter
from .models import Paper, PipelineOutput
from .queries import query_set_hash
from .report import render_markdown
from .sources import ArxivClient, HTTPConfig, PubMedClient, RxivClient, SportRxivClient
from .state import append_run_log, load_seen, save_seen, update_seen
from .summarizer import summarize_ranked_papers


def _deduplicate(papers: list[Paper]) -> list[Paper]:
    selected: dict[str, Paper] = {}
    for paper in papers:
        key = paper.identifier
        existing = selected.get(key)
        if not existing:
            selected[key] = paper
            continue

        # Keep the newest record, with explicit version precedence for preprints.
        existing_version = int(existing.version or 0) if (existing.version or "").isdigit() else 0
        candidate_version = int(paper.version or 0) if (paper.version or "").isdigit() else 0

        if candidate_version > existing_version:
            selected[key] = paper
            continue

        if paper.published_date > existing.published_date:
            selected[key] = paper

    return list(selected.values())


def _quality_checks(summaries) -> list[str]:
    problems: list[str] = []
    seen_identifiers: set[str] = set()

    for summary in summaries:
        identifier = summary.paper.identifier
        if identifier in seen_identifiers:
            problems.append(f"duplicate summary entry: {identifier}")
        seen_identifiers.add(identifier)

        if not summary.paper.citation_link and not summary.paper.doi and not summary.paper.pmid:
            problems.append(f"missing identifier/link: {summary.paper.title}")

        if not summary.novel_value:
            problems.append(f"missing 'What's new' block: {summary.paper.title}")
        if not summary.caveats:
            problems.append(f"missing caveats block: {summary.paper.title}")

        if not summary.paper.abstract.strip() and "unavailable" not in summary.key_findings[0].lower():
            problems.append(f"abstract missing but not marked unavailable: {summary.paper.title}")

    return problems


def run_digest(config: ScoutConfig) -> PipelineOutput:
    run_date = datetime.utcnow().date()
    end_date = run_date
    start_date = end_date - timedelta(days=max(1, config.days_back) - 1)

    seen = load_seen(config.state_seen_file)

    http = HTTPConfig(
        timeout_seconds=config.request_timeout_seconds,
        retry_attempts=config.retry_attempts,
    )
    clients = [
        PubMedClient(http=http),
        RxivClient(http=http, server="biorxiv"),
        RxivClient(http=http, server="medrxiv"),
        SportRxivClient(http=http),
    ]
    if config.include_arxiv:
        clients.append(ArxivClient(http=http))

    all_papers: list[Paper] = []
    failures: list[str] = []
    counts_by_source: dict[str, int] = {}

    for client in clients:
        result = client.fetch(start_date=start_date, end_date=end_date, max_results=config.max_candidates_per_source)
        counts_by_source[result.source_name] = len(result.papers)
        all_papers.extend(result.papers)
        if result.failure:
            failures.append(f"{result.source_name}: {result.failure}")

    deduped = _deduplicate(all_papers)
    unseen = [paper for paper in deduped if paper.identifier not in seen]

    stage1 = stage1_relevance_filter(unseen, config)
    ranked = rank_papers(stage1, config)
    top_ranked, remainder = split_ranked(ranked, max_summaries=config.max_summaries_total)
    summaries = summarize_ranked_papers(top_ranked)

    quality_issues = _quality_checks(summaries)
    if quality_issues:
        failures.append("quality checks: " + " | ".join(quality_issues))

    markdown = render_markdown(
        run_date=run_date,
        start_date=start_date,
        end_date=end_date,
        source_names=[client.source_name for client in clients],
        candidate_count=len(deduped),
        summarized=summaries,
        other_ranked=remainder,
        failures=failures,
    )

    config.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = config.output_dir / f"weekly_muscle_digest_{run_date.isoformat()}.md"
    report_path.write_text(markdown, encoding="utf-8")

    seen_entries = [(summary.paper.identifier, summary.paper.title) for summary in summaries]
    updated_seen = update_seen(seen, seen_entries, seen_date=datetime.utcnow())
    save_seen(config.state_seen_file, updated_seen)

    run_entry = {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "window_start": start_date.isoformat(),
        "window_end": end_date.isoformat(),
        "query_set_hash": query_set_hash(config.include_keywords),
        "counts_by_source": counts_by_source,
        "candidate_count": len(deduped),
        "included_count": len(stage1),
        "summarized_count": len(summaries),
        "failures": failures,
    }
    append_run_log(config.run_log_file, run_entry)

    return PipelineOutput(
        report_path=str(report_path),
        summarized_count=len(summaries),
        candidate_count=len(deduped),
        included_count=len(stage1),
        sources_searched=[client.source_name for client in clients],
        failures=failures,
    )
