import dataclasses
import json
import unittest

from balalite.cards import Card, Rank, Suit
from balalite.consumables import CONSUMABLE_POOL
from balalite.game import GameState, MAX_CONSUMABLE_SLOTS, MAX_JOKER_SLOTS
from balalite.jokers import JOKER_POOL
from balalite.packs import PACK_POOL
from balalite.scoring import HandType


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


def consumable(key):
    return next(c for c in CONSUMABLE_POOL if c.key == key)


class TestNegativeJokerEdition(unittest.TestCase):
    def test_applying_negative_frees_up_a_slot(self):
        game = GameState(seed="neg-joker-slot")
        game.jokers = [joker("chip_stacker")] * MAX_JOKER_SLOTS
        game.consumables.append(consumable("editioner_negative_joker"))
        self.assertEqual(game.joker_slot_count(), MAX_JOKER_SLOTS)

        game.use_consumable(0, 0)

        self.assertEqual(game.jokers[0].edition, "negative")
        self.assertEqual(game.joker_slot_count(), MAX_JOKER_SLOTS - 1)
        self.assertEqual(len(game.jokers), MAX_JOKER_SLOTS)  # 조커 자체는 그대로 보유

    def test_buy_offer_allows_exceeding_slots_when_negative_present(self):
        game = GameState(seed="neg-joker-buy")
        game.jokers = [joker("chip_stacker")] * (MAX_JOKER_SLOTS - 1)
        game.jokers.append(dataclasses.replace(joker("almighty"), edition="negative"))
        game.money = 100
        game.shop_offers = [joker("grinder")]
        game.buy_offer(0)
        self.assertIn("구매 완료", game.shop_message)
        self.assertEqual(len(game.jokers), MAX_JOKER_SLOTS + 1)

    def test_joker_still_scores_normally_with_negative_edition(self):
        game = GameState(seed="neg-joker-scoring")
        game.jokers.append(dataclasses.replace(joker("joker_basic"), edition="negative"))
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4)


class TestNegativeConsumableEdition(unittest.TestCase):
    def test_cannot_target_self(self):
        game = GameState(seed="neg-consumable-self")
        game.consumables = [consumable("gold_charm"), consumable("editioner_negative_consumable")]
        message = game.use_consumable(1, 1)
        self.assertIn("자기 자신", message)
        self.assertEqual(len(game.consumables), 2)  # 아무것도 소모되지 않음

    def test_applying_negative_frees_up_consumable_slot(self):
        game = GameState(seed="neg-consumable-slot")
        game.consumables = [consumable("gold_charm"), consumable("editioner_negative_consumable")]
        self.assertEqual(game.consumable_slot_count(), MAX_CONSUMABLE_SLOTS)

        game.use_consumable(1, 0)

        self.assertEqual(len(game.consumables), 1)
        self.assertEqual(game.consumables[0].edition, "negative")
        self.assertEqual(game.consumable_slot_count(), 0)

    def test_pick_pack_item_allows_exceeding_slots_when_negative_present(self):
        game = GameState(seed="neg-pack")
        game.consumables = [dataclasses.replace(consumable("gold_charm"), edition="negative")] * MAX_CONSUMABLE_SLOTS
        pack = next(p for p in PACK_POOL if p.key == "pack_consumable")
        game._open_pack(pack)
        message = game.pick_pack_item(0)
        self.assertIn("획득", message)
        self.assertEqual(len(game.consumables), MAX_CONSUMABLE_SLOTS + 1)


class TestNegativeSaveLoad(unittest.TestCase):
    def test_edition_survives_save_load_round_trip(self):
        game = GameState(seed="neg-save")
        game.jokers.append(dataclasses.replace(joker("chip_stacker"), edition="negative"))
        game.consumables.append(dataclasses.replace(consumable("gold_charm"), edition="negative"))

        restored = GameState.from_dict(json.loads(json.dumps(game.to_dict())))

        self.assertEqual(restored.jokers[0].edition, "negative")
        self.assertEqual(restored.consumables[0].edition, "negative")
        self.assertEqual(restored.joker_slot_count(), 0)
        self.assertEqual(restored.consumable_slot_count(), 0)


if __name__ == "__main__":
    unittest.main()
