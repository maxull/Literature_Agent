from datetime import date
import unittest

from literature_scout.enrichment import assign_cluster, extract_methods_keywords
from literature_scout.models import Paper


class EnrichmentTests(unittest.TestCase):
    def test_assign_cluster_detects_disease_context(self) -> None:
        paper = Paper(
            title="Sarcopenia trajectories in aging skeletal muscle",
            authors=["A Author"],
            abstract="A clinical cohort study links inflammatory signatures to sarcopenia progression.",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Aging Cell",
            published_date=date(2026, 2, 20),
            year=2026,
            doi="10.1000/disease",
        )

        cluster = assign_cluster(paper)
        self.assertEqual(cluster, "Disease, Aging, and Clinical Translation")

    def test_extract_methods_keywords_detects_omics_and_insulin(self) -> None:
        paper = Paper(
            title="Spatial proteomics identifies insulin sensitivity programs",
            authors=["A Author"],
            abstract=(
                "We integrated spatial proteomics with transcriptomics and hyperinsulinemic-euglycemic clamp "
                "to profile skeletal muscle adaptation."
            ),
            source="PubMed",
            source_type="peer-reviewed",
            venue="Cell Metabolism",
            published_date=date(2026, 2, 20),
            year=2026,
            doi="10.1000/methods",
        )

        methods = extract_methods_keywords(paper, configured_keywords=["insulin sensitivity", "spatial proteomics"])
        self.assertIn("Spatial Proteomics", methods)
        self.assertIn("Transcriptomics", methods)
        self.assertIn("Insulin Sensitivity", methods)


if __name__ == "__main__":
    unittest.main()
