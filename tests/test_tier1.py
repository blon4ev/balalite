import unittest

from balalite.cards import Card, Rank, Suit
from balalite.game import GameState
from balalite.scoring import HandType
from balalite.tags import TAG_POOL
from balalite.vouchers import VOUCHER_POOL


def voucher(key):
    return next(v for v in VOUCHER_POOL if v.key == key)


def tag(key):
    return next(t for t in TAG_POOL if t.key == key)


class _FixedRandom:
    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


class TestInterest(unittest.TestCase):
    def test_interest_capped_and_added_on_blind_clear(self):
        game = GameState(seed="interest-test")
        game.money = 20
        game.round_score = 10 ** 9
        game._check_round_progress()
        # 보상 3+버리기(3) = 6 -> 26, 이자 min(26//5, 5)=5 -> 31
        self.assertEqual(game.last_reward, 6)
        self.assertEqual(game.last_interest, 5)
        self.assertEqual(game.money, 31)


class TestVouchers(unittest.TestCase):
    def test_hand_voucher_increases_base_hand_size(self):
        game = GameState(seed="voucher-hand")
        before = game.base_hand_size
        voucher("voucher_hand").effect(game)
        self.assertEqual(game.base_hand_size, before + 1)

    def test_discount_voucher_reduces_cost(self):
        game = GameState(seed="voucher-discount")
        voucher("voucher_discount").effect(game)
        self.assertEqual(game._discounted_cost(10), 8)


class TestBlindSkip(unittest.TestCase):
    def test_cannot_skip_boss_blind(self):
        game = GameState(seed="skip-boss")
        game.blind_index = 2
        self.assertFalse(game.can_skip_blind())

    def test_cannot_skip_after_acting(self):
        game = GameState(seed="skip-acted")
        game.discard_cards([0])
        self.assertFalse(game.can_skip_blind())

    def test_skip_advances_blind_without_playing(self):
        game = GameState(seed="skip-advance")
        self.assertTrue(game.can_skip_blind())
        game.skip_blind()
        self.assertEqual(game.blind_index, 1)
        self.assertIsNotNone(game.last_tag_message)

    def test_money_tag_grants_cash(self):
        game = GameState(seed="tag-money")
        before = game.money
        tag("money_tag").effect(game)
        self.assertEqual(game.money, before + 10)


class TestCardEnhancements(unittest.TestCase):
    def test_bonus_enhancement_adds_chips(self):
        game = GameState(seed="enh-bonus")
        cards = [Card(Rank.TWO, Suit.SPADES, enhancement="bonus")]
        _, chips, _, _, _ = game._score_cards(cards)
        self.assertEqual(chips, HandType.HIGH_CARD.base_chips + 2 + 30)

    def test_mult_enhancement_adds_mult(self):
        game = GameState(seed="enh-mult")
        cards = [Card(Rank.TWO, Suit.SPADES, enhancement="mult")]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4)

    def test_wild_enhancement_enables_mixed_suit_flush(self):
        game = GameState(seed="enh-wild")
        cards = [
            Card(Rank.TWO, Suit.SPADES, enhancement="wild"),
            Card(Rank.FOUR, Suit.HEARTS),
            Card(Rank.SIX, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.HEARTS),
            Card(Rank.TEN, Suit.HEARTS),
        ]
        hand_type, _, _, _, _ = game._score_cards(cards)
        self.assertEqual(hand_type, HandType.FLUSH)

    def test_glass_enhancement_doubles_mult(self):
        game = GameState(seed="enh-glass")
        game.rng = _FixedRandom(0.99)  # 파괴되지 않도록 고정
        cards = [Card(Rank.TWO, Suit.SPADES, enhancement="glass")]
        _, _, mult, _, destroyed = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult * 2)
        self.assertEqual(destroyed, [])

    def test_glass_enhancement_can_break(self):
        game = GameState(seed="enh-glass-break")
        game.rng = _FixedRandom(0.0)  # 항상 파괴되도록 고정
        card = Card(Rank.TWO, Suit.SPADES, enhancement="glass")
        _, _, _, _, destroyed = game._score_cards([card])
        self.assertEqual(destroyed, [card])


if __name__ == "__main__":
    unittest.main()
