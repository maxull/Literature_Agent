from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from literature_scout.pipeline import _existing_digest_has_summaries


class PipelineOutputGuardTests(unittest.TestCase):
    def _write_payload(self, tmp_dir: Path, payload: dict) -> Path:
        path = tmp_dir / "weekly_muscle_digest_2026-02-26.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_existing_digest_detected_when_papers_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            digest_path = self._write_payload(
                Path(tmp),
                {"coverage": {"summarized_count": 0}, "papers": [{"title": "x"}]},
            )
            self.assertTrue(_existing_digest_has_summaries(digest_path))

    def test_existing_digest_detected_when_coverage_count_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            digest_path = self._write_payload(
                Path(tmp),
                {"coverage": {"summarized_count": 3}, "papers": []},
            )
            self.assertTrue(_existing_digest_has_summaries(digest_path))

    def test_empty_digest_not_detected_as_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            digest_path = self._write_payload(
                Path(tmp),
                {"coverage": {"summarized_count": 0}, "papers": []},
            )
            self.assertFalse(_existing_digest_has_summaries(digest_path))


if __name__ == "__main__":
    unittest.main()
