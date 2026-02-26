from datetime import date
import unittest

from literature_scout.models import Paper, PaperSummary
from literature_scout.report import render_markdown


class ReportTests(unittest.TestCase):
    def test_report_contains_required_sections(self) -> None:
        paper = Paper(
            title="A skeletal muscle adaptation study",
            authors=["Alice One", "Bob Two", "Cara Three", "Dan Four"],
            abstract="This study tests a mechanism in skeletal muscle adaptation.",
            source="PubMed",
            source_type="peer-reviewed",
            venue="Journal",
            published_date=date(2026, 2, 21),
            year=2026,
            doi="10.1000/example",
            pmid="123456",
        )
        summary = PaperSummary(
            paper=paper,
            short_title="Skeletal muscle adaptation study",
            core_question="What controls adaptation in this model?",
            key_findings=["Finding 1"],
            mechanism=["Supported by causal evidence: pathway X -> Y"],
            known_before=["Prior work suggested pathway X may regulate adaptation."],
            novel_value=["Adds value by testing pathway X with perturbation."],
            implications=["Potential translational relevance for muscle disease."],
            caveats=["Needs validation in independent cohorts."],
            relevance="Directly relevant to skeletal muscle homeostasis.",
            evidence_class="causal",
        )

        markdown = render_markdown(
            run_date=date(2026, 2, 26),
            start_date=date(2026, 2, 20),
            end_date=date(2026, 2, 26),
            source_names=["PubMed", "biorxiv", "medrxiv", "sportRxiv"],
            candidate_count=11,
            summarized=[summary],
            other_ranked=[],
            failures=[],
        )

        self.assertIn("## Itinerary", markdown)
        self.assertIn("## Coverage", markdown)
        self.assertIn("## Highlights (Top 3-5)", markdown)
        self.assertIn("## Paper Summaries", markdown)
        self.assertIn("## Abstracts (Full)", markdown)
        self.assertIn("5) What's new here (novel added value)", markdown)
        self.assertIn("7) Caveats / open questions", markdown)


if __name__ == "__main__":
    unittest.main()
