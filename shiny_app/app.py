from __future__ import annotations

import json
from pathlib import Path
import re

from shiny import App, render, ui


REPO_ROOT = Path(__file__).resolve().parents[1]
DIGEST_DIR = REPO_ROOT / "reports" / "weekly_digests"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


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
        }

    latest = candidates[-1]
    return json.loads(latest.read_text(encoding="utf-8"))


DIGEST = _load_latest_digest()
CLUSTERS = DIGEST.get("clusters", {})
METHOD_INDEX = DIGEST.get("methods_index", {})


def _paper_card(paper: dict) -> ui.Tag:
    doi = paper.get("doi", "")
    doi_url = paper.get("doi_url", "")
    doi_line = (
        ui.p("DOI: ", ui.a(doi, href=doi_url, target="_blank"))
        if doi and doi_url
        else ui.p("DOI: unavailable")
    )

    key_visual_link = paper.get("key_visual_link", "")
    key_visual_line = (
        ui.p(
            "Key visual: ",
            ui.a(
                paper.get("key_visual_label", "Source visual"),
                href=key_visual_link,
                target="_blank",
            ),
        )
        if key_visual_link
        else ui.p("Key visual: unavailable")
    )

    return ui.card(
        ui.card_header(f"{paper.get('short_title', 'Untitled')} ({paper.get('year', '')})"),
        ui.p(f"{paper.get('discussion_summary', '')}"),
        ui.p(f"Cluster: {paper.get('cluster', '')} | Evidence: {paper.get('evidence_class', '')}"),
        ui.p(f"Methods: {', '.join(paper.get('methods_keywords', [])) or 'none detected'}"),
        doi_line,
        key_visual_line,
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


cluster_panels = []
for cluster_name, cluster_data in CLUSTERS.items():
    cluster_slug = _slugify(cluster_name)
    cluster_panels.append(
        ui.nav_panel(
            cluster_name,
            ui.h3(cluster_name),
            ui.p(cluster_data.get("chapter_summary", "No chapter summary available.")),
            ui.hr(),
            ui.h4("Highlighted papers"),
            ui.output_ui(f"highlights_{cluster_slug}"),
            ui.hr(),
            ui.h4("All papers in this cluster"),
            ui.output_ui(f"papers_{cluster_slug}"),
        )
    )

cluster_panels.append(
    ui.nav_panel(
        "Methods Index",
        ui.h3("Methods Keyword Index"),
        ui.output_ui("methods_index_view"),
    )
)

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.p("Search method keywords across all clusters."),
        ui.input_text("method_query", "Methods search", placeholder="e.g., spatial proteomics"),
        width="320px",
    ),
    ui.h2("Skeletal Muscle Literature Explorer"),
    ui.p(f"Digest date: {DIGEST.get('run_date', 'unavailable')}."),
    ui.p(
        "This interface groups papers by thematic clusters and presents chapter-style summaries with DOI-first links."
    ),
    ui.navset_tab(*cluster_panels),
    title="Muscle Literature Explorer",
)


def server(input, output, session):
    for cluster_name, cluster_data in CLUSTERS.items():
        cluster_slug = _slugify(cluster_name)

        @output(id=f"highlights_{cluster_slug}")
        @render.ui
        def _render_highlights(cluster_name=cluster_name, cluster_data=cluster_data):
            papers = cluster_data.get("papers", [])
            filtered = _filtered_papers(papers, input.method_query())
            highlights = [paper for paper in filtered if paper.get("is_highlight")]
            if not highlights:
                return ui.p("No highlighted papers match the current method search.")
            return ui.div(*[_paper_card(paper) for paper in highlights])

        @output(id=f"papers_{cluster_slug}")
        @render.ui
        def _render_papers(cluster_name=cluster_name, cluster_data=cluster_data):
            papers = cluster_data.get("papers", [])
            filtered = _filtered_papers(papers, input.method_query())
            if not filtered:
                return ui.p("No papers in this cluster match the current method search.")
            return ui.div(*[_paper_card(paper) for paper in filtered])

    @output
    @render.ui
    def methods_index_view():
        query = input.method_query().strip().lower()
        method_blocks = []

        for keyword, items in METHOD_INDEX.items():
            if query and query not in keyword.lower():
                item_hit = any(
                    query in " ".join([item.get("short_title", ""), item.get("cluster", "")]).lower()
                    for item in items
                )
                if not item_hit:
                    continue

            links = []
            for item in items:
                doi = item.get("doi", "")
                doi_url = item.get("doi_url", "")
                label = f"{item.get('short_title', 'Untitled')} ({item.get('cluster', '')})"
                if doi and doi_url:
                    links.append(ui.tags.li(ui.a(label, href=doi_url, target="_blank")))
                else:
                    links.append(ui.tags.li(f"{label} — DOI unavailable"))

            method_blocks.append(ui.h4(keyword))
            method_blocks.append(ui.tags.ul(*links))

        if not method_blocks:
            return ui.p("No method keywords match the current search.")
        return ui.div(*method_blocks)


app = App(app_ui, server)
