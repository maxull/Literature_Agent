from __future__ import annotations

import json
import os
from typing import Any

import requests

from .config import ScoutConfig
from .models import Paper, PaperSummary


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None

    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            payload = json.loads(text[start : end + 1])
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            return None
    return None


def llm_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def llm_ready(config: ScoutConfig) -> bool:
    return config.use_llm_summaries and bool(llm_api_key())


def summarize_with_llm(
    paper: Paper,
    cluster: str,
    methods_keywords: list[str],
    ranking_reasons: list[str],
    config: ScoutConfig,
) -> dict[str, Any] | None:
    api_key = llm_api_key()
    if not config.use_llm_summaries or not api_key:
        return None

    endpoint = config.llm_api_base.rstrip("/") + "/chat/completions"

    system_prompt = (
        "You are a biomedical literature analyst for skeletal muscle science. "
        "Write concise, natural scientific prose (journal discussion tone). "
        "Do not invent facts. Use only provided metadata/abstract. "
        "If abstract is missing, state uncertainty explicitly. "
        "Avoid bullet style in the generated fields."
    )
    user_prompt = {
        "task": "Return one JSON object with requested fields.",
        "required_fields": [
            "short_title",
            "core_question",
            "discussion_summary",
            "key_findings",
            "mechanism",
            "known_before",
            "novel_value",
            "implications",
            "caveats",
            "relevance",
            "evidence_class",
            "key_visual_label",
        ],
        "field_constraints": {
            "short_title": "<= 95 characters",
            "core_question": "1-2 sentences",
            "discussion_summary": "chapter-style narrative (~300 words) with background science then integration of new findings",
            "key_findings": "one paragraph, evidence-aware, no bullets",
            "mechanism": "one paragraph, clearly separate supported vs speculative",
            "known_before": "one paragraph, cautious where uncertain",
            "novel_value": "one paragraph, concrete added value",
            "implications": "one paragraph, biological/translational meaning",
            "caveats": "one paragraph including one high-value follow-up",
            "relevance": "1-2 sentences tying to skeletal muscle regulation",
            "evidence_class": "one of causal, associative, correlative, computational, observational, mixed",
            "key_visual_label": "short label for best available visual link",
        },
        "paper": {
            "title": paper.title,
            "authors": paper.authors,
            "venue": paper.venue,
            "year": paper.year,
            "source": paper.source,
            "study_type": paper.study_type,
            "abstract": paper.abstract or "Abstract unavailable.",
            "identifier": paper.identifier,
            "citation_link": paper.citation_link,
        },
        "context": {
            "cluster": cluster,
            "methods_keywords": methods_keywords,
            "ranking_reasons": ranking_reasons,
        },
    }

    payload = {
        "model": config.llm_model,
        "temperature": config.llm_temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=True)},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        endpoint,
        headers=headers,
        json=payload,
        timeout=config.llm_timeout_seconds,
    )
    response.raise_for_status()
    body = response.json()

    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    parsed = _extract_json_payload(content)
    if not parsed:
        return None
    return parsed


def summarize_cluster_with_llm(
    cluster: str,
    items: list[PaperSummary],
    config: ScoutConfig,
) -> str | None:
    api_key = llm_api_key()
    if not config.use_llm_summaries or not api_key or not items:
        return None

    endpoint = config.llm_api_base.rstrip("/") + "/chat/completions"
    payload_items = []
    for item in items[:12]:
        payload_items.append(
            {
                "title": item.paper.title,
                "venue": item.paper.venue,
                "year": item.paper.year,
                "evidence_class": item.evidence_class,
                "methods_keywords": item.methods_keywords,
                "discussion_summary": item.discussion_summary,
            }
        )

    system_prompt = (
        "You are drafting a scientific chapter update for skeletal muscle researchers. "
        "Write a coherent, factual chapter-style summary (~300 words), contextualizing prior knowledge and integrating new findings. "
        "Do not invent facts not present in the provided inputs."
    )
    user_prompt = {
        "cluster": cluster,
        "instruction": (
            "Provide a concise chapter-style summary with background context followed by integration of the new papers."
        ),
        "papers": payload_items,
    }

    body = {
        "model": config.llm_model,
        "temperature": config.llm_temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=True)},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        endpoint,
        headers=headers,
        json=body,
        timeout=config.llm_timeout_seconds,
    )
    response.raise_for_status()
    content = (
        response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    )
    cleaned = content.strip()
    return cleaned or None
