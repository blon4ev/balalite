import unittest

from balalite.cards import Card, Rank, Suit
from balalite.jokers import JOKER_POOL, apply_jokers
from balalite.scoring import HandType


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


class TestApplyJokers(unittest.TestCase):
    def test_additive_before_multiplicative(self):
        cards = [Card(Rank.KING, Suit.SPADES)] * 5
        owned = [joker("joker_basic"), joker("high_stakes")]
        chips, mult = apply_jokers(owned, cards, cards, HandType.HIGH_CARD, chips=10, mult=1)
        # +4 mult 먼저 적용 -> 5, 이후 x1.5 -> 7.5
        self.assertEqual(chips, 10)
        self.assertAlmostEqual(mult, 7.5)

    def test_suit_conditional_effect(self):
        cards = [Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.HEARTS), Card(Rank.FOUR, Suit.CLUBS)]
        owned = [joker("heart_lover")]
        chips, mult = apply_jokers(owned, cards, cards, HandType.HIGH_CARD, chips=5, mult=1)
        self.assertEqual(chips, 5)
        self.assertEqual(mult, 1 + 3 * 2)


if __name__ == "__main__":
    unittest.main()
