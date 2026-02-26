from __future__ import annotations

import json
from pathlib import Path
import re

from shiny import App, render, ui


REPO_ROOT = Path(__file__).resolve().parents[1]
DIGEST_DIR = REPO_ROOT / "reports" / "weekly_digests"


def _safe_id(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    if not cleaned:
        cleaned = "cluster"
    return f"cluster_{cleaned}"


def _to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_latest_digest() -> dict:
    candidates = sorted(DIGEST_DIR.glob("weekly_muscle_digest_*.json"))
    if not candidates:
        return {
            "run_date": "unavailable",
            "coverage": {},
            "clusters": {},
            "highlights": [],
            "methods_index": {},
            "papers": [],
            "search_terms": [],
            "active_journal_tiers": [],
        }

    latest = candidates[-1]
    return json.loads(latest.read_text(encoding="utf-8"))


DIGEST = _load_latest_digest()
COVERAGE = DIGEST.get("coverage", {})
CLUSTERS = DIGEST.get("clusters", {})
METHOD_INDEX = DIGEST.get("methods_index", {})
SEARCH_TERMS = DIGEST.get("search_terms", [])
ACTIVE_TIERS = DIGEST.get("active_journal_tiers", [])

SOURCES_SEARCHED = COVERAGE.get("sources_searched", [])
COUNTS_BY_SOURCE = COVERAGE.get("counts_by_source", {})
CANDIDATE_COUNT = _to_int(COVERAGE.get("candidate_count", 0))
INCLUDED_COUNT = _to_int(COVERAGE.get("included_count", COVERAGE.get("summarized_count", 0)))
SUMMARIZED_COUNT = _to_int(COVERAGE.get("summarized_count", 0))
EXCLUDED_COUNT = _to_int(COVERAGE.get("excluded_after_relevance", max(0, CANDIDATE_COUNT - INCLUDED_COUNT)))
RANKED_OUT_COUNT = _to_int(
    COVERAGE.get("not_summarized_after_ranking", max(0, INCLUDED_COUNT - SUMMARIZED_COUNT))
)


def _paper_card(paper: dict) -> ui.Tag:
    title = paper.get("title", "Untitled")
    authors = paper.get("authors", []) or []
    authors_text = ", ".join(authors) if authors else "Authors unavailable"
    header_line = (
        f"{paper.get('published_date', '')} | {paper.get('year', '')} | {paper.get('venue', '')}"
    )

    doi = paper.get("doi", "")
    doi_url = paper.get("doi_url", "")
    doi_line = (
        ui.p("DOI: ", ui.a(doi, href=doi_url, target="_blank"), class_="meta-line")
        if doi and doi_url
        else ui.p("DOI unavailable", class_="meta-line")
    )

    return ui.card(
        ui.card_header(title),
        ui.p(header_line, class_="meta-line"),
        ui.p(paper.get("discussion_summary", ""), class_="discussion-copy"),
        ui.p(authors_text, class_="meta-authors"),
        ui.p(
            f"Cluster: {paper.get('cluster', '')}",
            class_="meta-line",
        ),
        ui.p(
            f"Methods: {', '.join(paper.get('methods_keywords', [])) or 'none detected'}",
            class_="meta-line",
        ),
        ui.p(f"Evidence: {paper.get('evidence_class', '')}", class_="meta-line"),
        doi_line,
        class_="paper-card",
        full_screen=False,
    )


def _filtered_papers(papers: list[dict], method_query: str) -> list[dict]:
    query = method_query.strip().lower()
    if not query:
        return papers

    filtered: list[dict] = []
    for paper in papers:
        methods_blob = " ".join(paper.get("methods_keywords", [])).lower()
        if query in methods_blob:
            filtered.append(paper)
    return filtered


def _metric_card(label: str, value: str, sublabel: str) -> ui.Tag:
    return ui.div(
        ui.p(label, class_="metric-label"),
        ui.p(value, class_="metric-value"),
        ui.p(sublabel, class_="metric-sub"),
        class_="metric-card",
    )


def _source_breakdown_rows() -> list[ui.Tag]:
    rows: list[ui.Tag] = []
    if COUNTS_BY_SOURCE:
        source_items = sorted(COUNTS_BY_SOURCE.items(), key=lambda item: item[0].lower())
    else:
        source_items = [(source, 0) for source in SOURCES_SEARCHED]

    for source, count in source_items:
        rows.append(
            ui.tags.tr(
                ui.tags.td(source),
                ui.tags.td(str(count)),
            )
        )

    return rows


def _filter_row(label: str, value: int, total: int, tone: str) -> ui.Tag:
    pct = (100.0 * value / total) if total > 0 else 0.0
    width = f"{max(4.0, min(100.0, pct)):.1f}%" if value > 0 else "0%"
    return ui.div(
        ui.div(
            ui.p(label, class_="funnel-label"),
            ui.p(f"{value}", class_="funnel-value"),
            class_="funnel-head",
        ),
        ui.div(
            ui.div(style=f"width:{width}", class_=f"funnel-bar {tone}"),
            class_="funnel-track",
        ),
        ui.p(f"{pct:.1f}% of candidates", class_="funnel-sub"),
        class_="funnel-row",
    )


def _search_term_chips(limit: int = 60) -> list[ui.Tag]:
    terms = SEARCH_TERMS or []
    shown = terms[:limit]
    chips = [ui.span(term, class_="chip") for term in shown]
    if len(terms) > limit:
        chips.append(ui.span(f"+{len(terms) - limit} more", class_="chip chip-muted"))
    return chips


cluster_panels = [
    ui.nav_panel(
        "Overview",
        ui.div(
            _metric_card("Sources searched", str(len(SOURCES_SEARCHED)), "Databases and preprint servers queried"),
            _metric_card("Candidates identified", str(CANDIDATE_COUNT), "Deduplicated records after retrieval"),
            _metric_card("Passed relevance filter", str(INCLUDED_COUNT), "Stage 1 inclusion by muscle relevance"),
            _metric_card("Summarized in app", str(SUMMARIZED_COUNT), "Ranked and retained for narrative synthesis"),
            class_="metrics-grid",
        ),
        ui.div(
            ui.card(
                ui.card_header("Search Scope"),
                ui.p("Search terms", class_="section-label"),
                ui.div(*_search_term_chips(), class_="chip-wrap"),
                ui.p(
                    f"Active journal tiers: {', '.join(ACTIVE_TIERS) if ACTIVE_TIERS else 'not reported'}",
                    class_="section-note",
                ),
                class_="overview-card",
            ),
            ui.card(
                ui.card_header("Where Papers Were Identified"),
                ui.tags.table(
                    ui.tags.thead(ui.tags.tr(ui.tags.th("Source"), ui.tags.th("Records"))),
                    ui.tags.tbody(*_source_breakdown_rows()),
                    class_="stats-table",
                ),
                class_="overview-card",
            ),
            ui.card(
                ui.card_header("Filtering Funnel"),
                _filter_row("Candidates", CANDIDATE_COUNT, max(CANDIDATE_COUNT, 1), "tone-a"),
                _filter_row("After relevance filter", INCLUDED_COUNT, max(CANDIDATE_COUNT, 1), "tone-b"),
                _filter_row("Summarized output", SUMMARIZED_COUNT, max(CANDIDATE_COUNT, 1), "tone-c"),
                ui.p(f"Excluded after relevance: {EXCLUDED_COUNT}", class_="section-note"),
                ui.p(f"Not summarized after ranking cap: {RANKED_OUT_COUNT}", class_="section-note"),
                class_="overview-card",
            ),
            class_="overview-grid",
        ),
        ui.output_ui("coverage_alerts"),
    )
]

for cluster_name, cluster_data in CLUSTERS.items():
    cluster_slug = _safe_id(cluster_name)
    cluster_panels.append(
        ui.nav_panel(
            cluster_name,
            ui.h3(cluster_name, class_="cluster-title"),
            ui.p(cluster_data.get("chapter_summary", "No chapter summary available."), class_="chapter-copy"),
            ui.hr(class_="cluster-sep"),
            ui.h4("Highlighted Papers", class_="section-title"),
            ui.output_ui(f"highlights_{cluster_slug}"),
            ui.hr(class_="cluster-sep"),
            ui.h4("All Papers in this Cluster", class_="section-title"),
            ui.output_ui(f"papers_{cluster_slug}"),
        )
    )

cluster_panels.append(
    ui.nav_panel(
        "Methods Index",
        ui.h3("Methods Keyword Index", class_="cluster-title"),
        ui.p("Searchable across all clusters.", class_="section-note"),
        ui.output_ui("methods_index_view"),
    )
)

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.p("Theme", class_="sidebar-label"),
        ui.input_switch("theme_mode", "Use Slate Mode (lighter)", value=False),
        ui.hr(),
        ui.p("Methods search", class_="sidebar-label"),
        ui.input_text("method_query", "", placeholder="e.g., spatial proteomics"),
        ui.p("Filter cluster tabs and methods index by method keywords.", class_="sidebar-note"),
        width="320px",
    ),
    ui.tags.head(
        ui.tags.style(
            """
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=IBM+Plex+Mono:wght@500&display=swap');

            :root[data-theme='dark'] {
              --bg: #0f131a;
              --surface: #171d27;
              --surface-2: #1f2734;
              --stroke: #2f3b4d;
              --text: #e8edf6;
              --muted: #9eadc4;
              --accent: #4ec7a8;
              --accent-2: #5ea3ff;
              --chip-bg: #202a39;
              --shadow: 0 18px 50px rgba(4, 8, 14, 0.45);
            }

            :root[data-theme='slate'] {
              --bg: #d9e1ec;
              --surface: #e8edf4;
              --surface-2: #dfe6f1;
              --stroke: #b7c4d8;
              --text: #192435;
              --muted: #4f6079;
              --accent: #0f8f74;
              --accent-2: #236fd4;
              --chip-bg: #d1dbe9;
              --shadow: 0 14px 32px rgba(40, 58, 82, 0.16);
            }

            html, body {
              background: var(--bg) !important;
              color: var(--text) !important;
              font-family: 'Manrope', 'Avenir Next', 'Segoe UI', sans-serif;
            }

            .bslib-page-sidebar,
            .bslib-sidebar-layout,
            .main {
              background: var(--bg) !important;
              color: var(--text) !important;
            }

            .main *,
            .sidebar * {
              color: inherit;
            }

            .sidebar {
              background: var(--surface) !important;
              border-right: 1px solid var(--stroke) !important;
              color: var(--text) !important;
            }

            .nav {
              gap: 0.4rem;
            }

            .nav-pills .nav-link {
              border-radius: 999px;
              color: var(--muted);
              background: var(--surface);
              border: 1px solid var(--stroke);
              font-weight: 700;
            }

            .nav-pills .nav-link.active {
              color: var(--text);
              background: linear-gradient(135deg, var(--accent), var(--accent-2));
              border-color: transparent;
              box-shadow: var(--shadow);
            }

            .metric-card,
            .overview-card,
            .paper-card {
              background: var(--surface);
              border: 1px solid var(--stroke);
              border-radius: 18px;
              box-shadow: var(--shadow);
              color: var(--text) !important;
            }

            .card,
            .card-body,
            .card-header,
            .card p,
            .card h1,
            .card h2,
            .card h3,
            .card h4,
            .card h5,
            .card h6,
            label,
            th,
            td,
            .form-label,
            .control-label {
              color: var(--text) !important;
            }

            .form-control,
            .form-switch .form-check-input {
              background-color: var(--surface-2);
              border-color: var(--stroke);
              color: var(--text);
            }

            .metrics-grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
              gap: 0.9rem;
              margin-bottom: 1rem;
            }

            .metric-card {
              padding: 1rem 1.1rem;
            }

            .metric-label {
              margin: 0;
              color: var(--muted);
              text-transform: uppercase;
              font-size: 0.72rem;
              letter-spacing: 0.05em;
              font-weight: 800;
            }

            .metric-value {
              margin: 0.25rem 0 0.15rem 0;
              font-size: 2rem;
              line-height: 1.1;
              font-weight: 800;
            }

            .metric-sub {
              margin: 0;
              color: var(--muted);
              font-size: 0.82rem;
            }

            .overview-grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
              gap: 1rem;
            }

            .overview-card {
              padding: 1rem 1.05rem;
            }

            .chip-wrap {
              display: flex;
              flex-wrap: wrap;
              gap: 0.45rem;
            }

            .chip {
              display: inline-block;
              padding: 0.26rem 0.62rem;
              border-radius: 999px;
              background: var(--chip-bg);
              border: 1px solid var(--stroke);
              font-size: 0.78rem;
              font-family: 'IBM Plex Mono', monospace;
            }

            .chip-muted {
              color: var(--muted);
            }

            .stats-table {
              width: 100%;
              border-collapse: collapse;
            }

            .stats-table th,
            .stats-table td {
              border-bottom: 1px solid var(--stroke);
              padding: 0.5rem 0.25rem;
              font-size: 0.9rem;
            }

            .stats-table th {
              color: var(--muted);
              font-weight: 700;
              text-transform: uppercase;
              font-size: 0.72rem;
              letter-spacing: 0.04em;
            }

            .funnel-row {
              margin-bottom: 0.65rem;
            }

            .funnel-head {
              display: flex;
              align-items: baseline;
              justify-content: space-between;
            }

            .funnel-label {
              margin: 0;
              font-size: 0.88rem;
              color: var(--muted);
            }

            .funnel-value {
              margin: 0;
              font-family: 'IBM Plex Mono', monospace;
              font-size: 0.95rem;
            }

            .funnel-track {
              width: 100%;
              height: 0.62rem;
              border-radius: 999px;
              background: var(--surface-2);
              border: 1px solid var(--stroke);
              overflow: hidden;
              margin-top: 0.2rem;
            }

            .funnel-bar {
              height: 100%;
              border-radius: 999px;
            }

            .tone-a { background: linear-gradient(90deg, #54a2ff, #2f7de7); }
            .tone-b { background: linear-gradient(90deg, #49d1b0, #2ea98a); }
            .tone-c { background: linear-gradient(90deg, #f7c767, #e19a39); }

            .funnel-sub,
            .section-note,
            .sidebar-note {
              margin: 0.18rem 0 0 0;
              color: var(--muted);
              font-size: 0.78rem;
            }

            .section-title,
            .cluster-title {
              font-weight: 800;
              letter-spacing: 0.01em;
              color: var(--text) !important;
            }

            .chapter-copy,
            .discussion-copy {
              line-height: 1.72;
              font-size: 0.99rem;
            }

            .paper-card .card-header {
              font-size: 1.03rem;
              font-weight: 800;
              line-height: 1.3;
              margin-bottom: 0.1rem;
              padding-bottom: 0.2rem;
            }

            .paper-card .card-body {
              padding-top: 0.65rem;
            }

            .meta-authors {
              color: var(--muted);
              font-size: 0.9rem;
              margin-top: 0.35rem;
              margin-bottom: 0.2rem;
            }

            .meta-line {
              color: var(--muted);
              font-size: 0.82rem;
              margin: 0.08rem 0;
            }

            .discussion-copy {
              margin-top: 0.35rem;
              margin-bottom: 0.3rem;
            }

            .paper-sep,
            .cluster-sep {
              border-color: var(--stroke);
              opacity: 1;
            }

            .sidebar-label {
              margin: 0;
              text-transform: uppercase;
              font-size: 0.72rem;
              letter-spacing: 0.05em;
              font-weight: 800;
              color: var(--muted);
            }

            a {
              color: var(--accent-2);
            }
            """
        ),
        ui.tags.script(
            """
            document.addEventListener('DOMContentLoaded', () => {
              const root = document.documentElement;
              const applyTheme = (useSlate) => {
                root.setAttribute('data-theme', useSlate ? 'slate' : 'dark');
              };

              applyTheme(false);

              const toggle = document.getElementById('theme_mode');
              if (toggle) {
                toggle.checked = false;
                toggle.addEventListener('change', () => applyTheme(toggle.checked));
              }
            });
            """
        ),
    ),
    ui.h2("Muscle Litterature Explorer - by Max Ullrich"),
    ui.p(
        f"Digest date: {DIGEST.get('run_date', 'unavailable')} | "
        f"Coverage: {COVERAGE.get('window_start', 'n/a')} to {COVERAGE.get('window_end', 'n/a')}",
        class_="section-note",
    ),
    ui.navset_pill(*cluster_panels),
)


def server(input, output, session):
    for cluster_name, cluster_data in CLUSTERS.items():
        cluster_slug = _safe_id(cluster_name)

        @output(id=f"highlights_{cluster_slug}")
        @render.ui
        def _render_highlights(cluster_data=cluster_data):
            papers = cluster_data.get("papers", [])
            filtered = _filtered_papers(papers, input.method_query())
            highlights = [paper for paper in filtered if paper.get("is_highlight")]
            if not highlights:
                return ui.p("No highlighted papers match the current method search.", class_="section-note")
            return ui.div(*[_paper_card(paper) for paper in highlights])

        @output(id=f"papers_{cluster_slug}")
        @render.ui
        def _render_papers(cluster_data=cluster_data):
            papers = cluster_data.get("papers", [])
            filtered = _filtered_papers(papers, input.method_query())
            if not filtered:
                return ui.p("No papers in this cluster match the current method search.", class_="section-note")
            return ui.div(*[_paper_card(paper) for paper in filtered])

    @output
    @render.ui
    def methods_index_view():
        query = input.method_query().strip().lower()
        method_blocks: list[ui.Tag] = []

        for keyword, items in METHOD_INDEX.items():
            if query and query not in keyword.lower():
                item_hit = any(
                    query in " ".join(
                        [item.get("title", ""), item.get("short_title", ""), item.get("cluster", "")]
                    ).lower()
                    for item in items
                )
                if not item_hit:
                    continue

            links = []
            for item in items:
                doi = item.get("doi", "")
                doi_url = item.get("doi_url", "")
                label = f"{item.get('title', item.get('short_title', 'Untitled'))} ({item.get('cluster', '')})"
                if doi and doi_url:
                    links.append(ui.tags.li(ui.a(label, href=doi_url, target="_blank")))
                else:
                    links.append(ui.tags.li(f"{label} — DOI unavailable"))

            method_blocks.append(ui.h4(keyword))
            method_blocks.append(ui.tags.ul(*links))

        if not method_blocks:
            return ui.p("No method keywords match the current search.", class_="section-note")
        return ui.div(*method_blocks)

    @output
    @render.ui
    def coverage_alerts():
        failures = COVERAGE.get("failures", [])
        if not failures:
            return ui.div()

        return ui.card(
            ui.card_header("Source/Run Issues"),
            ui.tags.ul(*[ui.tags.li(issue) for issue in failures]),
            class_="overview-card",
        )


app = App(app_ui, server)
