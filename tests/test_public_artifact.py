from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ptcg_solution.feature_contract import FeatureContractError, validate_rows  # noqa: E402
from ptcg_solution.ranker import rank_order, score_rows, select_top_k  # noqa: E402


class PublicSourceTests(unittest.TestCase):
    def test_fixed_width_contract(self) -> None:
        validate_rows([[0.0] * 361, [1.0] * 361])
        with self.assertRaises(FeatureContractError):
            validate_rows([[0.0] * 360])

    def test_pure_tree_score(self) -> None:
        pure = {
            "feature_count": 2,
            "models": {
                "main": [
                    ([1, 0, 0], [2, 0, 0], [0, -1, -1], [0.5, 0.0, 0.0], [None, None, None], [0.0, 2.0, -1.0])
                ]
            },
        }
        self.assertEqual(score_rows(pure, "main", [[0.25, 0.0], [0.75, 0.0]]), [2.0, -1.0])

    def test_stable_selection_and_ranking(self) -> None:
        scores = [1.0, 1.0, 0.5]
        self.assertEqual(rank_order(scores), [0, 1, 2])
        self.assertEqual(select_top_k(scores, 1, 2), [0, 1])

    def test_restricted_payloads_are_absent(self) -> None:
        forbidden = (
            ROOT / "models" / "bronze_ranker.pkl",
            ROOT / "models" / "bronze_ranker.schema.json",
            ROOT / "submission" / "deck.csv",
            ROOT / "submission" / "main.py",
        )
        for path in forbidden:
            self.assertFalse(path.exists(), path)

    def test_public_python_has_no_engine_import(self) -> None:
        for path in (ROOT / "src").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("from cg", text)
            self.assertNotIn("import cg", text)


if __name__ == "__main__":
    unittest.main()
