from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+/'().-]*")

# Style anchor from user-provided target example (~300 words, chapter-like narrative).
EXAMPLE_TEXT = """
AMP-activated protein kinase (AMPK) is a heterotrimeric energy sensor that couples cellular energetic stress to metabolic control in skeletal muscle, including glucose uptake, fatty acid oxidation, and longer-term remodeling with exercise training. Full AMPK activation requires phosphorylation of the catalytic alpha-subunit at threonine 172 (T172) by upstream kinases such as LKB1 or CaMKKb. Prior genetic models that delete AMPK subunits have produced mixed conclusions about the necessity of AMPKa2 in exercise metabolism, in part because deletion perturbs holoenzyme stoichiometry and can induce compensation.

To resolve this, the authors generated global nonactivatable knock-in mice in which T172 is replaced by alanine (T172A), preserving protein abundance but preventing activation. Ampka2 T172A mice (but not Ampka1 T172A) showed a clear physiological phenotype, including increased fat-to-lean mass, reduced activity, impaired endurance exercise capacity, and markedly impaired skeletal muscle mitochondrial respiration and conductance. Integrated temporal multiomics (proteomics, phosphoproteomics, metabolomics) in gastrocnemius at rest, after 10 minutes of running, and at exhaustion was used to map how loss of AMPKa2 activation reshapes exercise responses.

The phosphoproteome analysis identified exercise-responsive phosphorylation sites that were activated in wild-type muscle but not properly activated in Ampka2 T172A muscle, spanning calcium handling, sarcomere proteins, muscle architecture, protein degradation pathways, and metabolic regulators. Motif analysis further prioritized a subset as putative direct AMPK targets, highlighting candidates that link AMPK to both contractile machinery and metabolic signaling during exercise.

Overall, this study updates the field by providing stoichiometry-preserving genetic evidence that AMPKa2 T172 phosphorylation is not merely correlated with exercise stress, but is mechanistically required to maintain baseline mitochondrial and bioenergetic machinery and to coordinate glycolytic and oxidative flux, mitochondrial function, and contractile performance during exercise.
"""
EXAMPLE_WORD_COUNT = len(WORD_RE.findall(EXAMPLE_TEXT))

BACKGROUND_MARKERS = (
    "prior",
    "historically",
    "has been",
    "is a",
    "known",
    "established",
    "background",
)
INTEGRATION_MARKERS = (
    "this study",
    "the authors",
    "to resolve",
    "overall",
    "collectively",
    "together",
    "in this work",
    "these findings",
)
EVIDENCE_MARKERS = (
    "using",
    "analysis",
    "data",
    "cohort",
    "mouse",
    "knock",
    "proteomics",
    "metabolomics",
    "phosphoproteomics",
    "single-cell",
    "intervention",
    "perturb",
)


def sentence_count(text: str) -> int:
    chunks = [segment.strip() for segment in SENTENCE_SPLIT.split(text.strip()) if segment.strip()]
    return len(chunks)


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def _validate_chapter_style(
    label: str,
    text: str,
    min_words: int,
    max_words: int,
    require_evidence_markers: bool,
) -> list[str]:
    errors: list[str] = []
    stripped = text.strip()
    lowered = stripped.lower()
    words = word_count(stripped)
    sentences = sentence_count(stripped)

    if words < min_words or words > max_words:
        errors.append(
            f"{label} word count {words} outside expected range {min_words}-{max_words} "
            f"(target style anchored to ~{EXAMPLE_WORD_COUNT} words)."
        )

    if sentences < 4:
        errors.append(f"{label} is too short in sentence structure ({sentences} sentences).")

    if any(line.lstrip().startswith(("-", "*")) for line in stripped.splitlines() if line.strip()):
        errors.append(f"{label} contains bullet-style lines; expected narrative prose.")

    if not any(marker in lowered for marker in BACKGROUND_MARKERS):
        errors.append(f"{label} missing clear background-context language.")

    if not any(marker in lowered for marker in INTEGRATION_MARKERS):
        errors.append(f"{label} missing explicit integration/update language.")

    if require_evidence_markers and not any(marker in lowered for marker in EVIDENCE_MARKERS):
        errors.append(f"{label} missing evidence/method framing language.")

    return errors


def validate_digest(path: Path) -> list[str]:
    errors: list[str] = []
    payload = json.loads(path.read_text(encoding="utf-8"))

    clusters = payload.get("clusters", {})
    if not isinstance(clusters, dict):
        return ["clusters field missing or invalid"]

    cluster_min = int(EXAMPLE_WORD_COUNT * 0.45)
    cluster_max = int(EXAMPLE_WORD_COUNT * 1.6)
    paper_min = int(EXAMPLE_WORD_COUNT * 0.60)
    paper_max = int(EXAMPLE_WORD_COUNT * 1.8)

    for cluster_name, cluster_data in clusters.items():
        chapter = str(cluster_data.get("chapter_summary", "")).strip()
        errors.extend(
            _validate_chapter_style(
                label=f"Cluster '{cluster_name}' chapter_summary",
                text=chapter,
                min_words=cluster_min,
                max_words=cluster_max,
                require_evidence_markers=False,
            )
        )

    papers = payload.get("papers", [])
    for paper in papers:
        title = paper.get("short_title") or paper.get("title") or "Untitled"
        discussion = str(paper.get("discussion_summary", "")).strip()
        errors.extend(
            _validate_chapter_style(
                label=f"Paper '{title}' discussion_summary",
                text=discussion,
                min_words=paper_min,
                max_words=paper_max,
                require_evidence_markers=True,
            )
        )

        doi = str(paper.get("doi", "")).strip()
        doi_url = str(paper.get("doi_url", "")).strip()
        if doi and doi_url != f"https://doi.org/{doi}":
            errors.append(f"DOI URL mismatch for '{title}'")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_digest_enrichment.py <path-to-digest-json>")
        return 2

    path = Path(sys.argv[1]).resolve()
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    errors = validate_digest(path)
    if errors:
        print("Validation failed:")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("Validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
