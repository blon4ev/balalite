import json
import unittest
from unittest import mock

from balalite.cards import Card, Rank, Suit
from balalite.consumables import CONSUMABLE_POOL
from balalite.game import GameState
from balalite.jokers import JOKER_POOL
from balalite.packs import PACK_POOL
from balalite.scoring import HandType


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


def consumable(key):
    return next(c for c in CONSUMABLE_POOL if c.key == key)


def pack(key):
    return next(p for p in PACK_POOL if p.key == key)


class TestBoosterPacks(unittest.TestCase):
    def test_opening_joker_pack_offers_choices(self):
        game = GameState(seed="pack-open")
        game.money = 100
        game.phase = "shop"
        game._open_pack(pack("pack_joker"))
        self.assertEqual(game.phase, "pack")
        self.assertEqual(len(game.pending_pack["items"]), 3)
        self.assertEqual(game.pending_pack["remaining"], 1)

    def test_picking_item_adds_to_inventory_and_returns_to_shop(self):
        game = GameState(seed="pack-pick")
        game._open_pack(pack("pack_joker"))
        chosen = game.pending_pack["items"][0]
        game.pick_pack_item(0)
        self.assertIn(chosen, game.jokers)
        self.assertEqual(game.phase, "shop")
        self.assertIsNone(game.pending_pack)

    def test_jumbo_pack_requires_two_picks_before_returning(self):
        game = GameState(seed="pack-jumbo")
        game._open_pack(pack("pack_consumable_jumbo"))
        game.pick_pack_item(0)
        self.assertEqual(game.phase, "pack")
        game.pick_pack_item(0)
        self.assertEqual(game.phase, "shop")
        self.assertEqual(len(game.consumables), 2)

    def test_skip_pack_returns_to_shop_without_picking(self):
        game = GameState(seed="pack-skip")
        game._open_pack(pack("pack_joker"))
        game.skip_pack()
        self.assertEqual(game.phase, "shop")
        self.assertEqual(game.jokers, [])

    def test_pick_fails_when_slot_full(self):
        game = GameState(seed="pack-full")
        game.jokers = [joker("joker_basic")] * 5
        game._open_pack(pack("pack_joker"))
        message = game.pick_pack_item(0)
        self.assertIn("가득", message)
        self.assertEqual(len(game.jokers), 5)


class TestSeals(unittest.TestCase):
    def test_red_seal_retriggers_enhancement_bonus(self):
        game = GameState(seed="seal-red")
        cards = [Card(Rank.TWO, Suit.SPADES, enhancement="mult", seal="red")]
        _, _, mult, _, _ = game._score_cards(cards)
        # 기본 mult(1) + mult 강화(4)*2(레트리거) = 9
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4 * 2)

    def test_gold_seal_grants_money_on_play(self):
        game = GameState(seed="seal-gold")
        game.hand[0].seal = "gold"
        before = game.money
        game.play_cards([0])
        self.assertEqual(game.phase, "blind")  # 이 정도 점수로는 블라인드를 깰 수 없음
        self.assertEqual(game.money, before + 3)

    def test_blue_seal_grants_consumable_on_discard(self):
        game = GameState(seed="seal-blue")
        game.hand[0].seal = "blue"
        before = len(game.consumables)
        game.discard_cards([0])
        self.assertEqual(len(game.consumables), before + 1)

    def test_sealer_applies_seal_to_target_card(self):
        game = GameState(seed="sealer-test")
        target = game.hand[0]
        consumable("sealer_gold").effect(game, target)
        self.assertEqual(target.seal, "gold")


class TestSaveLoad(unittest.TestCase):
    def _tmp_paths(self, tmp_path):
        return tmp_path / "save.json"

    def test_round_trip_preserves_state_and_rng_continuation(self):
        game = GameState(seed="save-test")
        game.money = 42
        game.jokers.append(joker("chip_stacker"))
        game.consumables.append(consumable("gold_charm"))
        game.hand_levels[HandType.PAIR] = 2
        game.owned_vouchers.add("voucher_hand")
        game.hand[0].enhancement = "glass"
        game.hand[0].edition = "foil"
        game.hand[0].seal = "red"

        data = game.to_dict()
        serialized = json.dumps(data)  # JSON 직렬화 가능한지 확인
        restored = GameState.from_dict(json.loads(serialized))

        self.assertEqual(restored.money, 42)
        self.assertEqual([j.key for j in restored.jokers], ["chip_stacker"])
        self.assertEqual([c.key for c in restored.consumables], ["gold_charm"])
        self.assertEqual(restored.hand_levels[HandType.PAIR], 2)
        self.assertIn("voucher_hand", restored.owned_vouchers)
        self.assertEqual(restored.hand[0].enhancement, "glass")
        self.assertEqual(restored.hand[0].edition, "foil")
        self.assertEqual(restored.hand[0].seal, "red")

        # RNG 상태가 이어져서 이후 뽑는 카드가 원본과 동일해야 함
        expected_next_draw = game.deck.draw(3)
        actual_next_draw = restored.deck.draw(3)
        self.assertEqual(expected_next_draw, actual_next_draw)

    def test_save_and_load_via_file(self):
        from balalite import save

        game = GameState(seed="save-file-test")
        game.money = 77
        with mock.patch.object(save, "SAVE_PATH", save.SAVE_DIR / "test_save_tmp.json"):
            save.SAVE_DIR.mkdir(parents=True, exist_ok=True)
            try:
                self.assertFalse(save.has_save())
                save.save_game(game)
                self.assertTrue(save.has_save())
                loaded = save.load_game()
                self.assertEqual(loaded.money, 77)
                save.delete_save()
                self.assertFalse(save.has_save())
            finally:
                save.delete_save()


if __name__ == "__main__":
    unittest.main()
