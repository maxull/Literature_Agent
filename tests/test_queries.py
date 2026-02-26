import unittest

from literature_scout.queries import build_pubmed_query, query_set_hash


class QueryTests(unittest.TestCase):
    def test_build_pubmed_query_with_journal_filters(self) -> None:
        query = build_pubmed_query(
            extra_keywords=["myokine"],
            journal_filters=["Cell Metabolism", "Nature Metabolism"],
        )
        self.assertIn('"myokine"[Title/Abstract]', query)
        self.assertIn('"Cell Metabolism"[Journal]', query)
        self.assertIn('"Nature Metabolism"[Journal]', query)
        self.assertIn("AND", query)

    def test_query_hash_changes_with_active_tiers(self) -> None:
        tiers = {
            "tier_1": ["Cell Metabolism"],
            "tier_2": ["Nature"],
        }
        hash_a = query_set_hash(extra_keywords=["cachexia"], journal_tiers=tiers, active_tiers=["tier_1"])
        hash_b = query_set_hash(extra_keywords=["cachexia"], journal_tiers=tiers, active_tiers=["tier_2"])
        self.assertNotEqual(hash_a, hash_b)


if __name__ == "__main__":
    unittest.main()
