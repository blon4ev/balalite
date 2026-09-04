import json
import unittest

from balalite.blinds import BOSS_EFFECTS, Blind, make_blinds
from balalite.cards import Card, Rank, Suit
from balalite.cli import InputError, _handle_blind_command
from balalite.decks import DECK_POOL, deck_by_key
from balalite.game import GameState, MAX_CONSUMABLE_SLOTS, MAX_JOKER_SLOTS
from balalite.jokers import JOKER_POOL
from balalite.scoring import HandType
from balalite.stakes import STAKE_POOL


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


def boss_effect(name):
    return next(e for e in BOSS_EFFECTS if e.name == name)


class TestSlotVouchersAndReroll(unittest.TestCase):
    def test_joker_slot_voucher_increases_max_slots(self):
        game = GameState(seed="voucher-joker-slot")
        before = game.max_joker_slots
        from balalite.vouchers import VOUCHER_POOL

        v = next(v for v in VOUCHER_POOL if v.key == "voucher_joker_slot")
        v.effect(game)
        self.assertEqual(game.max_joker_slots, before + 1)

    def test_consumable_slot_voucher_increases_max_slots(self):
        game = GameState(seed="voucher-consumable-slot")
        before = game.max_consumable_slots
        from balalite.vouchers import VOUCHER_POOL

        v = next(v for v in VOUCHER_POOL if v.key == "voucher_consumable_slot")
        v.effect(game)
        self.assertEqual(game.max_consumable_slots, before + 1)

    def test_reroll_cost_increases_each_reroll_and_resets_next_shop(self):
        game = GameState(seed="reroll-escalation")
        game.money = 100
        game.phase = "shop"
        game._roll_shop_offers()
        base_cost = game.reroll_cost
        game.reroll_shop()
        self.assertEqual(game.reroll_cost, base_cost + 1)
        game.reroll_shop()
        self.assertEqual(game.reroll_cost, base_cost + 2)
        game._enter_shop()
        self.assertEqual(game.reroll_cost, game.base_reroll_cost)


class TestDeckTypes(unittest.TestCase):
    def test_merchant_deck_trades_hand_size_for_money(self):
        game = GameState(seed="deck-merchant", deck_key="deck_merchant")
        self.assertEqual(game.money, 4 + 7)
        self.assertEqual(game.base_hand_size, 8 - 1)

    def test_reckless_deck_extra_joker_slot_and_harder_blinds(self):
        game = GameState(seed="deck-reckless", deck_key="deck_reckless")
        self.assertEqual(game.max_joker_slots, MAX_JOKER_SLOTS + 1)
        self.assertAlmostEqual(game.blind_requirement_multiplier, 1.15)

    def test_alchemist_deck_extra_consumable_slot(self):
        game = GameState(seed="deck-alchemist", deck_key="deck_alchemist")
        self.assertEqual(game.max_consumable_slots, MAX_CONSUMABLE_SLOTS + 1)

    def test_recruit_deck_starts_with_a_common_joker(self):
        game = GameState(seed="deck-recruit", deck_key="deck_recruit")
        self.assertEqual(len(game.jokers), 1)
        self.assertEqual(game.jokers[0].rarity, "common")

    def test_wild_deck_pre_enhances_deck_cards(self):
        game = GameState(seed="deck-wild", deck_key="deck_wild")
        enhanced = sum(1 for c in game.deck.cards if c.enhancement)
        self.assertEqual(enhanced, 5)

    def test_unknown_deck_key_falls_back_to_standard(self):
        self.assertEqual(deck_by_key("no_such_deck").key, "deck_standard")

    def test_all_decks_are_constructible(self):
        for d in DECK_POOL:
            game = GameState(seed=f"deck-smoke-{d.key}", deck_key=d.key)
            self.assertGreaterEqual(game.money, 0)
            self.assertGreaterEqual(game.base_hand_size, 1)


class TestStakes(unittest.TestCase):
    def test_stake_one_has_no_extra_effects(self):
        game = GameState(seed="stake-1", stake_level=1)
        self.assertEqual(game.base_discards, 3)
        self.assertEqual(game.max_joker_slots, MAX_JOKER_SLOTS)
        self.assertFalse(game.intensify_boss)

    def test_stake_two_removes_small_blind_reward(self):
        game = GameState(seed="stake-2", stake_level=2)
        game.round_score = game.current_blind.requirement
        game.discards_left = 3
        game._check_round_progress()
        self.assertEqual(game.last_reward, 0)

    def test_stake_three_increases_blind_requirement(self):
        game = GameState(seed="stake-3", stake_level=3)
        self.assertAlmostEqual(game.blind_requirement_multiplier, 1.10)

    def test_stake_four_reduces_discards(self):
        game = GameState(seed="stake-4", stake_level=4)
        self.assertEqual(game.base_discards, 3 - 1)

    def test_stake_five_reduces_joker_slot_and_intensifies_boss(self):
        game = GameState(seed="stake-5", stake_level=5)
        self.assertEqual(game.max_joker_slots, MAX_JOKER_SLOTS - 1)
        self.assertTrue(game.intensify_boss)

    def test_stake_level_out_of_range_clamps(self):
        game = GameState(seed="stake-clamp", stake_level=99)
        self.assertEqual(game.stake_level, len(STAKE_POOL))


class TestBossEffectExpansion(unittest.TestCase):
    def test_boss_effect_count_grew_well_beyond_original_eight(self):
        self.assertGreaterEqual(len(BOSS_EFFECTS), 16)

    def test_max_cards_per_play_blocks_oversized_plays_via_cli(self):
        game = GameState(seed="mcp-test")
        game.blinds[game.blind_index] = Blind(
            "boss", "test", 10_000_000, boss_effect("굳은 손가락")
        )
        with self.assertRaises(InputError):
            _handle_blind_command(game, "p", ["1", "2", "3"])
        # 허용된 장수는 정상 동작
        _handle_blind_command(game, "p", ["1", "2"])
        self.assertEqual(game.plays_left, game.base_plays - 1)

    def test_joker_mult_scale_halves_joker_mult_contribution(self):
        game = GameState(seed="jms-test")
        game.blinds[game.blind_index] = Blind(
            "boss", "test", 100, boss_effect("메아리 없는 방")
        )
        game.jokers.append(joker("joker_basic"))  # +4 Mult
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        expected = HandType.HIGH_CARD.base_mult + (4 * 0.5)
        self.assertAlmostEqual(mult, expected)

    def test_debuff_ranks_zeroes_chip_contribution(self):
        game = GameState(seed="debuff-rank-test")
        game.blinds[game.blind_index] = Blind(
            "boss", "test", 100, boss_effect("얼굴 없는 왕국")
        )
        _, chips, _, _, _ = game._score_cards([Card(Rank.KING, Suit.SPADES)])
        self.assertEqual(chips, HandType.HIGH_CARD.base_chips)

    def test_intensify_boss_makes_effects_harsher(self):
        intensified = make_blinds(9, intensify_boss=True)[2].boss_effect
        normal = make_blinds(9, intensify_boss=False)[2].boss_effect
        self.assertEqual(normal.name, intensified.name)
        if normal.money_tax:
            self.assertGreater(intensified.money_tax, normal.money_tax)


class TestDeckStakeSaveLoad(unittest.TestCase):
    def test_deck_and_stake_survive_save_load_round_trip(self):
        game = GameState(seed="save-deck-stake", deck_key="deck_reckless", stake_level=4)
        game.max_joker_slots += 2
        game.reroll_cost += 3

        restored = GameState.from_dict(json.loads(json.dumps(game.to_dict())))

        self.assertEqual(restored.deck_key, "deck_reckless")
        self.assertEqual(restored.stake_level, 4)
        self.assertEqual(restored.max_joker_slots, game.max_joker_slots)
        self.assertEqual(restored.reroll_cost, game.reroll_cost)
        self.assertAlmostEqual(restored.blind_requirement_multiplier, game.blind_requirement_multiplier)


if __name__ == "__main__":
    unittest.main()
