from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    source: str
    source_type: str
    venue: str
    published_date: date
    year: int
    doi: Optional[str] = None
    pmid: Optional[str] = None
    preprint_id: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    version: Optional[str] = None
    study_type: str = "unspecified"
    tags: list[str] = field(default_factory=list)
    is_review: bool = False

    @property
    def identifier(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower()}"
        if self.pmid:
            return f"pmid:{self.pmid}"
        if self.preprint_id:
            return f"preprint:{self.preprint_id.lower()}"
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id.lower()}"
        # Final fallback keeps report generation stable even when identifiers are missing.
        fallback = f"{self.source}:{self.title}:{self.published_date.isoformat()}"
        return f"fallback:{fallback.lower()}"

    @property
    def citation_link(self) -> str:
        if self.doi:
            return f"https://doi.org/{self.doi}"
        if self.pmid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        if self.url:
            return self.url
        return ""


@dataclass
class SourceFetchResult:
    source_name: str
    papers: list[Paper]
    failure: Optional[str] = None


@dataclass
class RankedPaper:
    paper: Paper
    score: float
    reasons: list[str]


@dataclass
class PaperSummary:
    paper: Paper
    short_title: str
    core_question: str
    key_findings: list[str]
    mechanism: list[str]
    known_before: list[str]
    novel_value: list[str]
    implications: list[str]
    caveats: list[str]
    relevance: str
    evidence_class: str
    cluster: str = "Skeletal Muscle Homeostasis and Adaptation"
    methods_keywords: list[str] = field(default_factory=list)
    key_visual_label: str = "Source page"
    key_visual_link: str = ""


@dataclass
class PipelineOutput:
    report_path: str
    summarized_count: int
    candidate_count: int
    included_count: int
    sources_searched: list[str]
    failures: list[str]
