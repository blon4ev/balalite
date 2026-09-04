import json
import unittest

from balalite.cards import Card, Rank, Suit
from balalite.game import GameState
from balalite.jokers import JOKER_POOL
from balalite.scoring import HandType


def joker(key):
    return next(j for j in JOKER_POOL if j.key == key)


def clear_current_blind(game):
    game.round_score = game.current_blind.requirement
    game.discards_left = game.base_discards
    game._check_round_progress()


class TestCopyNeighborJokers(unittest.TestCase):
    def test_echo_conductor_replays_the_next_jokers_effect(self):
        game = GameState(seed="echo-conductor")
        game.jokers = [joker("echo_conductor"), joker("joker_basic")]  # joker_basic: +4 Mult
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4 * 2)

    def test_mirror_shard_replays_the_previous_jokers_effect(self):
        game = GameState(seed="mirror-shard")
        game.jokers = [joker("joker_basic"), joker("mirror_shard")]
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4 * 2)

    def test_copier_at_list_edge_does_nothing_extra(self):
        game = GameState(seed="echo-edge")
        game.jokers = [joker("joker_basic"), joker("echo_conductor")]  # 오른쪽에 아무도 없음
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4)  # 복제 없이 1번만 적용

    def test_copier_does_not_chain_into_another_copier(self):
        game = GameState(seed="echo-chain")
        game.jokers = [joker("echo_conductor"), joker("mirror_shard"), joker("joker_basic")]
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        # echo_conductor은 바로 옆(mirror_shard, 복제 조커)을 복제하지 않으므로
        # joker_basic 효과는 정상 1회분만 적용된다.
        self.assertEqual(mult, HandType.HIGH_CARD.base_mult + 4)


class TestStatefulJokers(unittest.TestCase):
    def test_chain_reaction_builds_up_on_consecutive_same_hand_type(self):
        game = GameState(seed="chain-reaction")
        game.jokers = [joker("chain_reaction")]
        mults = []
        for _ in range(4):
            _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
            mults.append(mult)
        base = HandType.HIGH_CARD.base_mult
        self.assertEqual(mults, [base, base, base + 3, base + 6])

    def test_chain_reaction_resets_on_different_hand_type(self):
        game = GameState(seed="chain-reaction-reset")
        game.jokers = [joker("chain_reaction")]
        for _ in range(3):
            game._score_cards([Card(Rank.TWO, Suit.SPADES)])  # 하이 카드 3연속 -> 카운터 쌓임
        pair_cards = [Card(Rank.FIVE, Suit.SPADES), Card(Rank.FIVE, Suit.HEARTS)]
        game._score_cards(pair_cards)  # 족보가 바뀌므로 이번엔 쌓인 보너스를 받고 리셋
        _, _, mult_next, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(mult_next, HandType.HIGH_CARD.base_mult)  # 리셋되어 보너스 없음

    def test_chain_reaction_resets_on_round_start(self):
        game = GameState(seed="chain-reaction-round")
        game.jokers = [joker("chain_reaction")]
        for _ in range(3):
            game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertGreater(game.stateful_joker_counters.get("chain_reaction", 0), 0)
        clear_current_blind(game)  # 다음 라운드로 진행 (상점 -> 다음 블라인드)
        game.continue_from_shop()
        self.assertEqual(game.stateful_joker_counters.get("chain_reaction", 0), 0)

    def test_growing_roots_accumulates_while_no_discard(self):
        game = GameState(seed="growing-roots")
        game.jokers = [joker("growing_roots")]
        base = HandType.HIGH_CARD.base_chips + Rank.TWO.chips
        _, chips1, _, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        _, chips2, _, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(chips1, base)
        self.assertEqual(chips2, base + 8)

    def test_growing_roots_resets_on_discard(self):
        game = GameState(seed="growing-roots-discard")
        game.jokers = [joker("growing_roots")]
        game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        game.discard_cards([0])
        base = HandType.HIGH_CARD.base_chips + Rank.TWO.chips
        _, chips_after, _, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(chips_after, base)

    def test_old_clockwork_grows_permanently_on_blind_clear(self):
        game = GameState(seed="old-clockwork")
        game.jokers = [joker("old_clockwork")]
        base = HandType.HIGH_CARD.base_mult
        _, _, mult_before, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        clear_current_blind(game)
        _, _, mult_after, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(mult_before, base)
        self.assertEqual(mult_after, base + 1)

    def test_old_clockwork_does_not_reset_on_round_start(self):
        game = GameState(seed="old-clockwork-persist")
        game.jokers = [joker("old_clockwork")]
        clear_current_blind(game)
        game.continue_from_shop()
        self.assertEqual(game.stateful_joker_counters.get("old_clockwork", 0), 1)

    def test_crumbling_hourglass_decays_on_blind_clear(self):
        game = GameState(seed="crumbling-hourglass")
        game.jokers = [joker("crumbling_hourglass")]
        base = HandType.HIGH_CARD.base_mult
        _, _, mult_before, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        clear_current_blind(game)
        _, _, mult_after, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertEqual(mult_before, base + 20)
        self.assertEqual(mult_after, base + 18)

    def test_war_cry_multiplies_with_cleared_blind_count(self):
        game = GameState(seed="war-cry")
        game.jokers = [joker("war_cry")]
        for _ in range(5):
            clear_current_blind(game)
            game.continue_from_shop()
        base = HandType.HIGH_CARD.base_mult
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertAlmostEqual(mult, base * (1 + 0.03 * 5))


class TestLateGameMultiplicativeJokers(unittest.TestCase):
    def test_ante_judgment_scales_with_ante_and_caps(self):
        game = GameState(seed="ante-judgment")
        game.jokers = [joker("ante_judgment")]
        base = HandType.HIGH_CARD.base_mult
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertAlmostEqual(mult, base * (1 + 0.1 * game.ante))
        game.ante = 50  # 상한 캡 확인
        _, _, mult_capped, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertAlmostEqual(mult_capped, base * 2.0)

    def test_joker_resonance_scales_with_joker_count(self):
        game = GameState(seed="joker-resonance")
        game.jokers = [joker("joker_resonance"), joker("chip_stacker"), joker("chip_stacker")]
        base = HandType.HIGH_CARD.base_mult
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertAlmostEqual(mult, base * min(2.5, 1 + 0.05 * 3))

    def test_compound_wizard_scales_with_money_and_caps(self):
        game = GameState(seed="compound-wizard")
        game.jokers = [joker("compound_wizard")]
        base = HandType.HIGH_CARD.base_mult
        game.money = 50
        _, _, mult, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertAlmostEqual(mult, base * (1 + 0.005 * 50))
        game.money = 10_000  # 상한 캡 확인
        _, _, mult_capped, _, _ = game._score_cards([Card(Rank.TWO, Suit.SPADES)])
        self.assertAlmostEqual(mult_capped, base * 2.0)


class TestSynergyStateSaveLoad(unittest.TestCase):
    def test_stateful_counters_survive_save_load_round_trip(self):
        game = GameState(seed="synergy-save")
        game.jokers = [joker("old_clockwork"), joker("chain_reaction")]
        clear_current_blind(game)
        game.continue_from_shop()
        for _ in range(3):
            game._score_cards([Card(Rank.TWO, Suit.SPADES)])

        restored = GameState.from_dict(json.loads(json.dumps(game.to_dict())))

        self.assertEqual(restored.stateful_joker_counters, game.stateful_joker_counters)
        self.assertEqual(restored.stateful_joker_meta, game.stateful_joker_meta)


if __name__ == "__main__":
    unittest.main()
