from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ScoutConfig:
    days_back: int
    max_candidates_per_source: int
    max_summaries_total: int
    include_keywords: list[str]
    exclude_keywords: list[str]
    preferred_topics: list[str]
    include_reviews: bool
    include_arxiv: bool
    output_dir: Path
    state_seen_file: Path
    run_log_file: Path
    request_timeout_seconds: int
    retry_attempts: int


DEFAULT_CONFIG = ScoutConfig(
    days_back=7,
    max_candidates_per_source=120,
    max_summaries_total=20,
    include_keywords=[],
    exclude_keywords=[],
    preferred_topics=[],
    include_reviews=True,
    include_arxiv=False,
    output_dir=Path("."),
    state_seen_file=Path("state_seen.json"),
    run_log_file=Path("run_log.json"),
    request_timeout_seconds=25,
    retry_attempts=3,
)


def load_config(config_path: str | Path = "config.yaml") -> ScoutConfig:
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_CONFIG

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    return ScoutConfig(
        days_back=int(raw.get("days_back", DEFAULT_CONFIG.days_back)),
        max_candidates_per_source=int(
            raw.get("max_candidates_per_source", DEFAULT_CONFIG.max_candidates_per_source)
        ),
        max_summaries_total=int(raw.get("max_summaries_total", DEFAULT_CONFIG.max_summaries_total)),
        include_keywords=list(raw.get("include_keywords", DEFAULT_CONFIG.include_keywords)),
        exclude_keywords=list(raw.get("exclude_keywords", DEFAULT_CONFIG.exclude_keywords)),
        preferred_topics=list(raw.get("preferred_topics", DEFAULT_CONFIG.preferred_topics)),
        include_reviews=bool(raw.get("include_reviews", DEFAULT_CONFIG.include_reviews)),
        include_arxiv=bool(raw.get("include_arxiv", DEFAULT_CONFIG.include_arxiv)),
        output_dir=Path(raw.get("output_dir", str(DEFAULT_CONFIG.output_dir))),
        state_seen_file=Path(raw.get("state_seen_file", str(DEFAULT_CONFIG.state_seen_file))),
        run_log_file=Path(raw.get("run_log_file", str(DEFAULT_CONFIG.run_log_file))),
        request_timeout_seconds=int(
            raw.get("request_timeout_seconds", DEFAULT_CONFIG.request_timeout_seconds)
        ),
        retry_attempts=int(raw.get("retry_attempts", DEFAULT_CONFIG.retry_attempts)),
    )
