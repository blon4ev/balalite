import unittest

from balalite.cards import Card, Rank, Suit
from balalite.consumables import CONSUMABLE_POOL, LEVEL_BONUS
from balalite.scoring import HandType, evaluate_hand


def wild(rank, suit):
    return Card(rank, suit, enhancement="wild")


class TestHiddenHands(unittest.TestCase):
    def test_normal_four_of_a_kind_without_wild_stays_four_of_a_kind(self):
        cards = [Card(Rank.KING, s) for s in Suit]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FOUR_OF_A_KIND)
        self.assertEqual(len(scoring), 4)

    def test_four_kings_plus_wild_becomes_five_of_a_kind(self):
        cards = [
            Card(Rank.KING, Suit.SPADES), Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS), Card(Rank.KING, Suit.CLUBS),
            wild(Rank.TWO, Suit.CLUBS),
        ]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FIVE_OF_A_KIND)
        self.assertEqual(len(scoring), 5)

    def test_three_kings_plus_two_wilds_becomes_five_of_a_kind(self):
        cards = [
            Card(Rank.KING, Suit.SPADES), Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.DIAMONDS),
            wild(Rank.TWO, Suit.CLUBS), wild(Rank.THREE, Suit.CLUBS),
        ]
        hand_type, _ = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FIVE_OF_A_KIND)

    def test_one_real_card_plus_four_wilds_becomes_flush_five(self):
        cards = [Card(Rank.KING, Suit.SPADES)] + [wild(Rank.TWO, Suit.CLUBS) for _ in range(4)]
        hand_type, _ = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FLUSH_FIVE)

    def test_five_of_a_kind_same_suit_real_cards_is_flush_five(self):
        # 표준 덱에서는 같은 무늬+같은 랭크 카드가 2장 있을 수 없으므로
        # 반드시 와일드가 대신 채워야 플러시 파이브가 나온다.
        cards = [Card(Rank.KING, Suit.SPADES)] + [wild(Rank.KING, Suit.HEARTS) for _ in range(4)]
        hand_type, _ = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FLUSH_FIVE)

    def test_full_house_with_mismatched_suits_stays_full_house(self):
        cards = [
            Card(Rank.KING, Suit.SPADES), Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.SEVEN, Suit.CLUBS), Card(Rank.SEVEN, Suit.DIAMONDS),
        ]
        hand_type, _ = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FULL_HOUSE)

    def test_full_house_unified_by_wild_suit_becomes_flush_house(self):
        cards = [
            Card(Rank.KING, Suit.SPADES),
            wild(Rank.KING, Suit.HEARTS),
            wild(Rank.KING, Suit.DIAMONDS),
            Card(Rank.SEVEN, Suit.SPADES),
            wild(Rank.SEVEN, Suit.DIAMONDS),
        ]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FLUSH_HOUSE)
        self.assertEqual(len(scoring), 5)


class TestRuneCoverage(unittest.TestCase):
    def test_level_bonus_covers_all_twelve_hand_types(self):
        self.assertEqual(len(LEVEL_BONUS), 12)
        for ht in HandType:
            self.assertIn(ht, LEVEL_BONUS)

    def test_rune_pool_has_twelve_entries(self):
        runes = [c for c in CONSUMABLE_POOL if c.kind == "rune"]
        self.assertEqual(len(runes), 12)
        hand_types = {r.hand_type for r in runes}
        self.assertEqual(hand_types, set(HandType))


if __name__ == "__main__":
    unittest.main()
