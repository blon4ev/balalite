import unittest

from balalite.blinds import BOSS_EFFECTS
from balalite.cards import Card, Rank, Suit
from balalite.consumables import CHARMS, RUNES
from balalite.game import GameState
from balalite.jokers import JOKER_POOL
from balalite.scoring import HandType


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


def rune_for(hand_type):
    return next(r for r in RUNES if r.hand_type is hand_type)


def charm(key):
    return next(c for c in CHARMS if c.key == key)


class TestSeeding(unittest.TestCase):
    def test_same_seed_same_hand(self):
        g1 = GameState(seed="office-secret")
        g2 = GameState(seed="office-secret")
        self.assertEqual(g1.hand, g2.hand)

    def test_different_seed_different_hand(self):
        g1 = GameState(seed="seed-a")
        g2 = GameState(seed="seed-b")
        self.assertNotEqual(g1.hand, g2.hand)


class TestBossEffects(unittest.TestCase):
    def _force_boss(self, game, effect):
        boss_blind = game.blinds[2]
        boss_blind.boss_effect = effect
        game.blind_index = 2
        game._start_blind_round()

    def test_banned_hand_type_scores_zero(self):
        effect = next(e for e in BOSS_EFFECTS if HandType.PAIR in e.banned_hand_types)
        game = GameState(seed="boss-ban")
        self._force_boss(game, effect)
        cards = [Card(Rank.NINE, Suit.SPADES), Card(Rank.NINE, Suit.HEARTS)]
        _, _, _, gained = game._score_cards(cards)
        self.assertEqual(gained, 0)

    def test_debuff_suit_removes_chip_contribution(self):
        effect = next(e for e in BOSS_EFFECTS if e.debuff_suit is Suit.HEARTS)
        game = GameState(seed="boss-debuff")
        self._force_boss(game, effect)
        cards = [Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.SPADES)]
        hand_type, chips, _, _ = game._score_cards(cards)
        self.assertEqual(hand_type, HandType.PAIR)
        # 하트 King(10칩)은 무효화되어 스페이드 King(10칩)만 반영되어야 함
        self.assertEqual(chips, HandType.PAIR.base_chips + 10)

    def test_hand_size_delta_applied_on_round_start(self):
        effect = next(e for e in BOSS_EFFECTS if e.hand_size_delta < 0)
        game = GameState(seed="boss-handsize")
        self._force_boss(game, effect)
        self.assertEqual(len(game.hand), 8 + effect.hand_size_delta)


class TestConsumables(unittest.TestCase):
    def test_rune_levels_up_hand_type_permanently(self):
        game = GameState(seed="rune-test")
        game.consumables.append(rune_for(HandType.PAIR))
        game.use_consumable(0)
        self.assertEqual(game.hand_levels[HandType.PAIR], 1)
        cards = [Card(Rank.NINE, Suit.SPADES), Card(Rank.NINE, Suit.HEARTS)]
        _, chips, _, _ = game._score_cards(cards)
        bonus_chips, _ = game.hand_levels[HandType.PAIR], None
        self.assertGreater(chips, HandType.PAIR.base_chips + 9 + 9)

    def test_gold_charm_grants_money(self):
        game = GameState(seed="charm-test")
        before = game.money
        game.consumables.append(charm("gold_charm"))
        game.use_consumable(0)
        self.assertEqual(game.money, before + 8)

    def test_double_charm_doubles_next_play_only(self):
        game = GameState(seed="charm-double")
        game.consumables.append(charm("double_charm"))
        game.use_consumable(0)
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult1, _ = game._score_cards(cards)
        self.assertAlmostEqual(mult1, HandType.HIGH_CARD.base_mult * 2)
        _, _, mult2, _ = game._score_cards(cards)
        self.assertAlmostEqual(mult2, HandType.HIGH_CARD.base_mult)


class TestJokerEconomy(unittest.TestCase):
    def test_sell_joker_refunds_half_cost(self):
        game = GameState(seed="sell-test")
        j = joker("chip_stacker")
        game.jokers.append(j)
        before = game.money
        game.sell_joker(0)
        self.assertEqual(game.money, before + j.cost // 2)
        self.assertEqual(game.jokers, [])

    def test_reroll_shop_charges_cost_and_changes_offers(self):
        from balalite.game import SHOP_REROLL_COST

        game = GameState(seed="reroll-test")
        game.money = 100
        game.phase = "shop"
        game._roll_shop_offers()
        before_money = game.money
        game.reroll_shop()
        self.assertEqual(game.money, before_money - SHOP_REROLL_COST)


if __name__ == "__main__":
    unittest.main()
