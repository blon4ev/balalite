import unittest

from balalite.cards import Card, Rank, Suit
from balalite.consumables import LEVEL_BONUS
from balalite.game import GameState
from balalite.jokers import JOKER_POOL
from balalite.scoring import HandType


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


class TestJokerPoolIntegrity(unittest.TestCase):
    def test_exactly_one_hundred_ten_jokers(self):
        # 100종 + 시너지 조커 10종(복제/누적형/후반 스케일링) = 110종
        self.assertEqual(len(JOKER_POOL), 110)

    def test_all_keys_unique(self):
        keys = [j.key for j in JOKER_POOL]
        self.assertEqual(len(keys), len(set(keys)))

    def test_all_costs_positive(self):
        self.assertTrue(all(j.cost > 0 for j in JOKER_POOL))


class TestSuitJokers(unittest.TestCase):
    def test_suit_chip_bonus_counts_played_cards(self):
        game = GameState(seed="suit-chip")
        game.jokers.append(joker("suit_chip_hearts"))
        cards = [Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.HEARTS), Card(Rank.FOUR, Suit.CLUBS)]
        _, chips, _, _, _ = game._score_cards(cards)
        self.assertEqual(chips, HandType.HIGH_CARD.base_chips + 4 + 16)

    def test_no_suit_bonus_only_when_absent(self):
        game = GameState(seed="no-suit")
        game.jokers.append(joker("no_suit_clubs"))
        with_club = [Card(Rank.TWO, Suit.CLUBS)]
        without_club = [Card(Rank.TWO, Suit.HEARTS)]
        _, _, mult1, _, _ = game._score_cards(with_club)
        _, _, mult2, _, _ = game._score_cards(without_club)
        self.assertEqual(mult1, HandType.HIGH_CARD.base_mult)
        self.assertEqual(mult2, HandType.HIGH_CARD.base_mult + 6)


class TestRankAndHandTypeJokers(unittest.TestCase):
    def test_queen_grace_requires_queen_in_scoring(self):
        game = GameState(seed="queen")
        game.jokers.append(joker("queen_grace"))
        cards = [Card(Rank.QUEEN, Suit.SPADES)]
        _, chips, _, _, _ = game._score_cards(cards)
        self.assertEqual(chips, HandType.HIGH_CARD.base_chips + 10 + 10)

    def test_hand_scholar_scales_with_rune_level(self):
        game = GameState(seed="scholar")
        game.jokers.append(joker("scholar_flush"))
        game.hand_levels[HandType.FLUSH] = 3
        cards = [
            Card(Rank.TWO, Suit.SPADES), Card(Rank.FOUR, Suit.SPADES), Card(Rank.SIX, Suit.SPADES),
            Card(Rank.EIGHT, Suit.SPADES), Card(Rank.TEN, Suit.SPADES),
        ]
        hand_type, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(hand_type, HandType.FLUSH)
        # 룬 레벨은 이미 게임 엔진이 기본 배수에 자동으로 반영하고(+level_mult/레벨),
        # 학자 조커가 그 위에 한 번 더 같은 양만큼 얹는다 (수집가 조커와 같은 중첩 설계).
        _, level_mult = LEVEL_BONUS[HandType.FLUSH]
        self.assertEqual(mult, HandType.FLUSH.base_mult + level_mult * 3 + 2 * 3)


class TestEnhancementEditionJokers(unittest.TestCase):
    def test_bonus_appraiser_counts_bonus_enhancement(self):
        game = GameState(seed="appraiser")
        game.jokers.append(joker("bonus_appraiser"))
        cards = [Card(Rank.TWO, Suit.SPADES, enhancement="bonus")]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 6)

    def test_poly_collector_multiplies_per_scoring_card(self):
        game = GameState(seed="poly-collector")
        game.jokers.append(joker("poly_collector"))
        cards = [
            Card(Rank.TWO, Suit.SPADES, edition="polychrome"),
            Card(Rank.TWO, Suit.HEARTS, edition="polychrome"),
        ]
        hand_type, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(hand_type, HandType.PAIR)
        # 폴리크롬 에디션은 카드별로 게임 엔진이 이미 Mult x1.5씩 곱하고(2장 -> x2.25),
        # poly_collector 조커가 그 이전 단계에서 카드 수만큼 추가로 배수를 곱한다.
        joker_factor = min(2.0, 1 + 0.15 * 2)
        builtin_edition_factor = 1.5 * 1.5
        self.assertAlmostEqual(mult, HandType.PAIR.base_mult * joker_factor * builtin_edition_factor)


class TestEconomyAndStateJokers(unittest.TestCase):
    def test_omega_joker_doubles_everything(self):
        game = GameState(seed="omega")
        game.jokers.append(joker("omega_joker"))
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, chips, mult, _, _ = game._score_cards(cards)
        self.assertEqual(chips, HandType.HIGH_CARD.base_chips * 2 + 2 * 2)  # (기본칩+카드값)*2
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult * 2)

    def test_last_stand_only_on_final_play(self):
        game = GameState(seed="last-stand")
        game.jokers.append(joker("last_stand"))
        game.plays_left = 2
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult_not_last, _, _ = game._score_cards(cards)
        game.plays_left = 1
        _, _, mult_last, _, _ = game._score_cards(cards)
        self.assertEqual(mult_not_last, HandType.HIGH_CARD.base_mult)
        self.assertEqual(mult_last, HandType.HIGH_CARD.base_mult * 2)

    def test_full_slots_bonus_requires_full_joker_slots(self):
        game = GameState(seed="full-slots")
        filler = joker("chip_stacker")
        game.jokers = [filler] * 4 + [joker("full_slots_bonus")]
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult * 1.5)

    def test_karma_scales_with_money_capped(self):
        game = GameState(seed="karma")
        game.jokers.append(joker("karma"))
        game.money = 1000
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertAlmostEqual(mult, HandType.HIGH_CARD.base_mult * 1.5)

    def test_retrigger_chips_adds_scoring_card_values_again(self):
        game = GameState(seed="retrigger")
        game.jokers.append(joker("retrigger_chips"))
        cards = [Card(Rank.KING, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        hand_type, chips, _, _, _ = game._score_cards(cards)
        self.assertEqual(hand_type, HandType.PAIR)
        base = HandType.PAIR.base_chips + 10 + 10
        self.assertEqual(chips, base + 20)


class TestPatternJokers(unittest.TestCase):
    def test_crimson_hand_requires_all_red(self):
        game = GameState(seed="crimson")
        game.jokers.append(joker("crimson_hand"))
        red_cards = [Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.DIAMONDS)]
        mixed_cards = [Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.CLUBS)]
        _, _, mult_red, _, _ = game._score_cards(red_cards)
        _, _, mult_mixed, _, _ = game._score_cards(mixed_cards)
        self.assertEqual(mult_red, HandType.HIGH_CARD.base_mult + 12)
        self.assertEqual(mult_mixed, HandType.HIGH_CARD.base_mult)

    def test_all_face_requires_only_face_or_ace(self):
        game = GameState(seed="all-face")
        game.jokers.append(joker("all_face"))
        cards = [Card(Rank.JACK, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
        _, chips, _, _, _ = game._score_cards(cards)
        self.assertEqual(chips, HandType.HIGH_CARD.base_chips + 11 + 18)

    def test_no_face_requires_absence_of_face_cards(self):
        game = GameState(seed="no-face")
        game.jokers.append(joker("no_face"))
        cards = [Card(Rank.TWO, Suit.SPADES)]
        _, _, mult, _, _ = game._score_cards(cards)
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 10)


if __name__ == "__main__":
    unittest.main()
