import unittest

from balalite.cards import Card, Rank, Suit
from balalite.consumables import CONSUMABLE_POOL
from balalite.game import GameState, _weighted_unique_sample
from balalite.jokers import JOKER_POOL, RARITY_WEIGHT
from balalite.scoring import HandType


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


def consumable(key):
    return next(c for c in CONSUMABLE_POOL if c.key == key)


class TestJokerExpansion(unittest.TestCase):
    def test_pool_has_at_least_thirty_jokers(self):
        self.assertGreaterEqual(len(JOKER_POOL), 30)

    def test_every_joker_has_known_rarity(self):
        for j in JOKER_POOL:
            self.assertIn(j.rarity, RARITY_WEIGHT)

    def test_unique_keys(self):
        keys = [j.key for j in JOKER_POOL]
        self.assertEqual(len(keys), len(set(keys)))

    def test_almighty_scales_with_scoring_card_count(self):
        game = GameState(seed="almighty-test")
        game.jokers.append(joker("almighty"))
        cards = [
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.NINE, Suit.CLUBS),
        ]
        hand_type, chips, mult, _, _ = game._score_cards(cards)
        self.assertEqual(hand_type, HandType.THREE_OF_A_KIND)
        self.assertEqual(chips, HandType.THREE_OF_A_KIND.base_chips + 27 + 5 * 3)
        self.assertEqual(mult, HandType.THREE_OF_A_KIND.base_mult + 2 * 3)


class TestWeightedSample(unittest.TestCase):
    def test_returns_unique_items_of_requested_size(self):
        import random

        rng = random.Random(42)
        items = list(range(20))
        weights = [1] * 20
        chosen = _weighted_unique_sample(rng, items, weights, 5)
        self.assertEqual(len(chosen), 5)
        self.assertEqual(len(set(chosen)), 5)


class TestSpectralCards(unittest.TestCase):
    def test_mist_doubles_joker_delta_only(self):
        game = GameState(seed="mist-test")
        game.jokers.append(joker("joker_basic"))  # +4 mult
        game.mist_active = True
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult, _, _ = game._score_cards(cards)
        # base_mult(1) + (joker 4 * 2) = 9
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4 * 2)

    def test_echo_adds_flat_mult(self):
        game = GameState(seed="echo-test")
        game.echo_mult_bonus = 2
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 2)

    def test_curse_enhances_random_hand_card(self):
        game = GameState(seed="curse-test")
        consumable("spectral_curse").effect(game)
        self.assertTrue(any(c.enhancement is not None for c in game.hand))

    def test_ruin_removes_card_permanently(self):
        game = GameState(seed="ruin-test")
        target = game.hand[0]
        before_size = len(game.hand)
        consumable("spectral_ruin").effect(game, target)
        self.assertNotIn(target, game.hand)
        self.assertEqual(len(game.hand), before_size)
        all_cards = game.hand + game.deck.cards + game.deck.discard_pile
        self.assertNotIn(target, all_cards)

    def test_fortune_grants_money(self):
        game = GameState(seed="fortune-test")
        before = game.money
        consumable("spectral_fortune").effect(game)
        self.assertEqual(game.money, before + 15)

    def test_clone_duplicates_owned_joker(self):
        game = GameState(seed="clone-test")
        game.jokers.append(joker("chip_stacker"))
        consumable("spectral_clone").effect(game)
        self.assertEqual(len(game.jokers), 2)
        self.assertEqual(game.jokers[0].key, game.jokers[1].key)

    def test_clone_grants_money_when_no_jokers(self):
        game = GameState(seed="clone-empty-test")
        before = game.money
        consumable("spectral_clone").effect(game)
        self.assertEqual(game.money, before + 10)


class TestCardEditions(unittest.TestCase):
    def test_foil_adds_chips(self):
        game = GameState(seed="foil-test")
        cards = [Card(Rank.TWO, Suit.SPADES, edition="foil")]
        _, chips, _, _, _ = game._score_cards(cards)
        self.assertEqual(chips, HandType.HIGH_CARD.base_chips + 2 + 50)

    def test_holographic_adds_mult(self):
        game = GameState(seed="holo-test")
        cards = [Card(Rank.TWO, Suit.SPADES, edition="holographic")]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 10)

    def test_polychrome_multiplies_mult(self):
        game = GameState(seed="poly-test")
        cards = [Card(Rank.TWO, Suit.SPADES, edition="polychrome")]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult * 1.5)

    def test_editioner_applies_edition_to_target_card(self):
        game = GameState(seed="editioner-test")
        target = game.hand[0]
        consumable("editioner_foil").effect(game, target)
        self.assertEqual(target.edition, "foil")


if __name__ == "__main__":
    unittest.main()
