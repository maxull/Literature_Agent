from datetime import date
from dataclasses import replace
import unittest

from literature_scout.config import DEFAULT_CONFIG
from literature_scout.filtering import rank_papers, stage1_relevance_filter
from literature_scout.models import Paper


class FilteringTests(unittest.TestCase):
    def test_stage1_includes_skeletal_muscle_mechanistic_study(self) -> None:
        paper = Paper(
            title="CRISPR knockout reveals autophagy control in skeletal muscle",
            authors=["A Author"],
            abstract="In mouse skeletal muscle, knockout of gene X altered myofiber autophagy.",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Journal",
            published_date=date(2026, 2, 20),
            year=2026,
            doi="10.1234/example",
        )

        result = stage1_relevance_filter([paper], DEFAULT_CONFIG)
        self.assertEqual(len(result), 1)
        self.assertIn("autophagy", " ".join(result[0].tags).lower())

    def test_stage1_excludes_non_mechanistic_coaching(self) -> None:
        paper = Paper(
            title="Sports psychology coaching improves confidence",
            authors=["A Author"],
            abstract="This coaching intervention focused on confidence and team motivation.",
            source="sportRxiv",
            source_type="preprint",
            venue="sportRxiv",
            published_date=date(2026, 2, 20),
            year=2026,
            doi="10.1234/coach",
        )

        config = replace(
            DEFAULT_CONFIG,
            exclude_keywords=DEFAULT_CONFIG.exclude_keywords + ["confidence"],
        )
        result = stage1_relevance_filter([paper], config)
        self.assertEqual(len(result), 0)

    def test_ranking_prefers_mechanistic_over_associative(self) -> None:
        mechanistic = Paper(
            title="Lineage tracing defines satellite cell program in skeletal muscle",
            authors=["A Author"],
            abstract="Using lineage tracing and knockout perturbation, we identify a causal pathway.",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Journal",
            published_date=date(2026, 2, 18),
            year=2026,
            doi="10.1234/mech",
        )
        associative = Paper(
            title="Association between circulating cytokines and muscle mass",
            authors=["B Author"],
            abstract="An observational cohort reports correlation between cytokines and sarcopenia.",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Journal",
            published_date=date(2026, 2, 18),
            year=2026,
            doi="10.1234/corr",
        )

        ranked = rank_papers([associative, mechanistic], DEFAULT_CONFIG)
        self.assertEqual(ranked[0].paper.doi, "10.1234/mech")

    def test_ranking_boosts_tier_1_journal(self) -> None:
        tier_1 = Paper(
            title="Skeletal muscle fiber signaling study",
            authors=["Tier One"],
            abstract="Mouse skeletal muscle knockout and lineage tracing identify pathway control.",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Cell Metabolism",
            published_date=date(2026, 2, 18),
            year=2026,
            doi="10.1234/tier1",
        )
        tier_3 = Paper(
            title="Skeletal muscle fiber signaling study",
            authors=["Tier Three"],
            abstract="Mouse skeletal muscle knockout and lineage tracing identify pathway control.",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Physiological Reports",
            published_date=date(2026, 2, 18),
            year=2026,
            doi="10.1234/tier3",
        )

        ranked = rank_papers([tier_3, tier_1], DEFAULT_CONFIG)
        self.assertEqual(ranked[0].paper.doi, "10.1234/tier1")


if __name__ == "__main__":
    unittest.main()
