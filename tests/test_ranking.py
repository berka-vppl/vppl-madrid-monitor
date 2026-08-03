import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ranking import calculate_score, get_priority


class RankingTests(unittest.TestCase):
    def test_preferred_penthouse_gets_maximum_priority(self):
        promotion = {
            "city": "Madrid",
            "bedrooms": 4,
            "penthouse": True,
            "price": 420000,
            "title": "Atico en Madrid",
        }
        score = calculate_score(promotion)
        self.assertEqual(score, 180)
        self.assertEqual(get_priority(score), "PRIORIDAD MÁXIMA")

    def test_basic_promotion_has_normal_priority(self):
        promotion = {
            "city": "Getafe",
            "bedrooms": 2,
            "penthouse": False,
            "price": None,
            "title": "Residencial Sur",
        }
        score = calculate_score(promotion)
        self.assertEqual(score, 0)
        self.assertEqual(get_priority(score), "PRIORIDAD NORMAL")


if __name__ == "__main__":
    unittest.main()
