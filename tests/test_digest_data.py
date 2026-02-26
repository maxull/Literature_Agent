from datetime import date
import unittest

from literature_scout.digest_data import build_digest_payload
from literature_scout.models import Paper, PaperSummary


class DigestDataTests(unittest.TestCase):
    def test_payload_uses_doi_links_for_papers(self) -> None:
        paper = Paper(
            title="Mechanistic study",
            authors=["A Author"],
            abstract="abstract",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Cell Metabolism",
            published_date=date(2026, 2, 20),
            year=2026,
            doi="10.1000/example",
        )
        summary = PaperSummary(
            paper=paper,
            short_title="Mechanistic study",
            core_question="core",
            key_findings=["findings"],
            mechanism=["mechanism"],
            known_before=["known"],
            novel_value=["novel"],
            implications=["implications"],
            caveats=["caveats"],
            relevance="relevance",
            evidence_class="causal",
            discussion_summary="chapter paragraph",
            cluster="Mechanistic Signaling and Proteostasis",
            methods_keywords=["Spatial Proteomics"],
        )

        payload = build_digest_payload(
            run_date=date(2026, 2, 26),
            start_date=date(2026, 2, 20),
            end_date=date(2026, 2, 26),
            source_names=["PubMed"],
            counts_by_source={"PubMed": 1},
            included_count=1,
            candidate_count=1,
            summaries=[summary],
            other_ranked=[],
            failures=[],
            cluster_chapters={"Mechanistic Signaling and Proteostasis": "chapter"},
            search_terms=["skeletal muscle", "proteomics"],
            active_journal_tiers=["tier_1"],
        )

        record = payload["papers"][0]
        self.assertEqual(record["doi_url"], "https://doi.org/10.1000/example")
        self.assertEqual(payload["methods_index"]["Spatial Proteomics"][0]["doi_url"], "https://doi.org/10.1000/example")


if __name__ == "__main__":
    unittest.main()
