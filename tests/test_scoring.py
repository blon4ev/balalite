import unittest

from balalite.cards import Card, Rank, Suit
from balalite.scoring import HandType, evaluate_hand


def c(rank, suit):
    return Card(rank, suit)


class TestEvaluateHand(unittest.TestCase):
    def test_high_card(self):
        cards = [c(Rank.TWO, Suit.SPADES), c(Rank.NINE, Suit.HEARTS), c(Rank.KING, Suit.CLUBS)]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.HIGH_CARD)
        self.assertEqual(scoring, [c(Rank.KING, Suit.CLUBS)])

    def test_pair(self):
        cards = [c(Rank.SEVEN, Suit.SPADES), c(Rank.SEVEN, Suit.HEARTS), c(Rank.TWO, Suit.CLUBS)]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.PAIR)
        self.assertEqual(len(scoring), 2)

    def test_two_pair(self):
        cards = [
            c(Rank.SEVEN, Suit.SPADES), c(Rank.SEVEN, Suit.HEARTS),
            c(Rank.KING, Suit.CLUBS), c(Rank.KING, Suit.DIAMONDS),
            c(Rank.TWO, Suit.SPADES),
        ]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.TWO_PAIR)
        self.assertEqual(len(scoring), 4)

    def test_three_of_a_kind(self):
        cards = [c(Rank.NINE, Suit.SPADES), c(Rank.NINE, Suit.HEARTS), c(Rank.NINE, Suit.CLUBS)]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.THREE_OF_A_KIND)
        self.assertEqual(len(scoring), 3)

    def test_straight(self):
        cards = [
            c(Rank.FIVE, Suit.SPADES), c(Rank.SIX, Suit.HEARTS), c(Rank.SEVEN, Suit.CLUBS),
            c(Rank.EIGHT, Suit.DIAMONDS), c(Rank.NINE, Suit.SPADES),
        ]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.STRAIGHT)
        self.assertEqual(len(scoring), 5)

    def test_ace_low_straight(self):
        cards = [
            c(Rank.ACE, Suit.SPADES), c(Rank.TWO, Suit.HEARTS), c(Rank.THREE, Suit.CLUBS),
            c(Rank.FOUR, Suit.DIAMONDS), c(Rank.FIVE, Suit.SPADES),
        ]
        hand_type, _ = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.STRAIGHT)

    def test_flush(self):
        cards = [
            c(Rank.TWO, Suit.SPADES), c(Rank.SIX, Suit.SPADES), c(Rank.NINE, Suit.SPADES),
            c(Rank.JACK, Suit.SPADES), c(Rank.KING, Suit.SPADES),
        ]
        hand_type, _ = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FLUSH)

    def test_full_house(self):
        cards = [
            c(Rank.NINE, Suit.SPADES), c(Rank.NINE, Suit.HEARTS), c(Rank.NINE, Suit.CLUBS),
            c(Rank.TWO, Suit.DIAMONDS), c(Rank.TWO, Suit.SPADES),
        ]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FULL_HOUSE)
        self.assertEqual(len(scoring), 5)

    def test_four_of_a_kind(self):
        cards = [
            c(Rank.NINE, Suit.SPADES), c(Rank.NINE, Suit.HEARTS),
            c(Rank.NINE, Suit.CLUBS), c(Rank.NINE, Suit.DIAMONDS),
        ]
        hand_type, scoring = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.FOUR_OF_A_KIND)
        self.assertEqual(len(scoring), 4)

    def test_straight_flush(self):
        cards = [
            c(Rank.FIVE, Suit.SPADES), c(Rank.SIX, Suit.SPADES), c(Rank.SEVEN, Suit.SPADES),
            c(Rank.EIGHT, Suit.SPADES), c(Rank.NINE, Suit.SPADES),
        ]
        hand_type, _ = evaluate_hand(cards)
        self.assertEqual(hand_type, HandType.STRAIGHT_FLUSH)


if __name__ == "__main__":
    unittest.main()
