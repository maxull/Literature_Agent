from __future__ import annotations

import json
import os
from typing import Any

import requests

from .config import ScoutConfig
from .models import Paper


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
