import random

from .blinds import MAX_ANTE, make_blinds
from .cards import Deck
from .consumables import CONSUMABLE_POOL, LEVEL_BONUS
from .jokers import JOKER_POOL, apply_jokers
from .scoring import evaluate_hand

HAND_SIZE = 8
PLAYS_PER_ROUND = 4
DISCARDS_PER_ROUND = 3
STARTING_MONEY = 4
MAX_JOKER_SLOTS = 5
MAX_CONSUMABLE_SLOTS = 2
SHOP_OFFER_COUNT = 4
SHOP_REROLL_COST = 2


class GameState:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.seed = seed
        self.deck = Deck(self.rng)
        self.ante = 1
        self.blinds = make_blinds(self.ante)
        self.blind_index = 0
        self.money = STARTING_MONEY
        self.jokers = []
        self.consumables = []
        self.hand_levels = {}
        self.hand = []
        self.hand_size = HAND_SIZE
        self.round_score = 0
        self.plays_left = PLAYS_PER_ROUND
        self.discards_left = DISCARDS_PER_ROUND
        self.next_play_mult_multiplier = 1
        self.phase = "blind"
        self.last_result = None
        self.last_reward = 0
        self.sort_mode = "rank"
        self.shop_offers = []
        self.shop_message = ""
        self._start_blind_round()

    @property
    def current_blind(self):
        return self.blinds[self.blind_index]

    @property
    def boss_effect(self):
        return self.current_blind.boss_effect

    def _start_blind_round(self):
        self.deck.reset()
        self.hand_size = HAND_SIZE
        self.plays_left = PLAYS_PER_ROUND
        self.discards_left = DISCARDS_PER_ROUND
        self.next_play_mult_multiplier = 1

        effect = self.boss_effect
        if effect:
            self.hand_size = max(1, self.hand_size + effect.hand_size_delta)
            self.plays_left = max(1, self.plays_left + effect.plays_delta)
            self.discards_left = max(0, self.discards_left + effect.discards_delta)
            self.money = max(0, self.money - effect.money_tax)

        self.hand = self.deck.draw(self.hand_size)
        self.sort_hand(self.sort_mode)
        self.round_score = 0
        self.phase = "blind"
        self.last_result = None

    def sort_hand(self, by="rank"):
        self.sort_mode = by
        if by == "rank":
            self.hand.sort(key=lambda c: c.rank.order, reverse=True)
        else:
            self.hand.sort(key=lambda c: (c.suit.name, -c.rank.order))

    def _score_cards(self, cards):
        hand_type, scoring_cards = evaluate_hand(cards)
        level = self.hand_levels.get(hand_type, 0)
        level_chips, level_mult = LEVEL_BONUS.get(hand_type, (0, 0))
        effect = self.boss_effect

        chip_sum = 0
        for c in scoring_cards:
            if effect and effect.debuff_suit and c.suit is effect.debuff_suit:
                continue
            chip_sum += c.rank.chips

        base_chips = hand_type.base_chips + level * level_chips + chip_sum
        base_mult = hand_type.base_mult + level * level_mult
        chips, mult = apply_jokers(self.jokers, cards, scoring_cards, hand_type, base_chips, base_mult)
        mult *= self.next_play_mult_multiplier
        self.next_play_mult_multiplier = 1

        if effect and hand_type in effect.banned_hand_types:
            gained = 0
        else:
            gained = int(chips * mult)
        return hand_type, chips, mult, gained

    def play_cards(self, indices):
        cards = [self.hand[i] for i in indices]
        hand_type, chips, mult, gained = self._score_cards(cards)
        self.round_score += gained

        for i in sorted(indices, reverse=True):
            del self.hand[i]
        self.hand.extend(self.deck.draw(len(indices)))
        self.sort_hand(self.sort_mode)

        self.plays_left -= 1
        self.last_result = (hand_type, chips, mult, gained)
        self._check_round_progress()

    def discard_cards(self, indices):
        for i in sorted(indices, reverse=True):
            del self.hand[i]
        self.hand.extend(self.deck.draw(len(indices)))
        self.sort_hand(self.sort_mode)
        self.discards_left -= 1
        self.last_result = None

    def use_consumable(self, index):
        if index < 0 or index >= len(self.consumables):
            return "잘못된 번호입니다."
        item = self.consumables.pop(index)
        item.effect(self)
        return f"'{item.name}' 사용 완료!"

    def sell_joker(self, index):
        if index < 0 or index >= len(self.jokers):
            return "잘못된 번호입니다."
        joker = self.jokers.pop(index)
        refund = joker.cost // 2
        self.money += refund
        return f"'{joker.name}' 판매 완료! (+${refund})"

    def _check_round_progress(self):
        if self.round_score >= self.current_blind.requirement:
            self.last_reward = 3 + self.discards_left
            self.money += self.last_reward
            self._enter_shop()
        elif self.plays_left <= 0:
            self.phase = "game_over"

    def _enter_shop(self):
        self.phase = "shop"
        self.shop_message = ""
        self._roll_shop_offers()

    def _roll_shop_offers(self):
        pool = list(JOKER_POOL) + list(CONSUMABLE_POOL)
        k = min(SHOP_OFFER_COUNT, len(pool))
        self.shop_offers = self.rng.sample(pool, k=k)

    def reroll_shop(self):
        if self.money < SHOP_REROLL_COST:
            self.shop_message = "돈이 부족합니다."
            return
        self.money -= SHOP_REROLL_COST
        self._roll_shop_offers()
        self.shop_message = "상점을 새로고침했습니다."

    def buy_offer(self, offer_index):
        if offer_index < 0 or offer_index >= len(self.shop_offers):
            self.shop_message = "잘못된 번호입니다."
            return
        item = self.shop_offers[offer_index]
        is_joker = hasattr(item, "timing")

        if is_joker and len(self.jokers) >= MAX_JOKER_SLOTS:
            self.shop_message = "조커 슬롯이 가득 찼습니다."
            return
        if not is_joker and len(self.consumables) >= MAX_CONSUMABLE_SLOTS:
            self.shop_message = "소모품 슬롯이 가득 찼습니다."
            return
        if self.money < item.cost:
            self.shop_message = "돈이 부족합니다."
            return

        self.money -= item.cost
        if is_joker:
            self.jokers.append(item)
        else:
            self.consumables.append(item)
        del self.shop_offers[offer_index]
        self.shop_message = f"'{item.name}' 구매 완료!"

    def continue_from_shop(self):
        if self.blind_index + 1 < len(self.blinds):
            self.blind_index += 1
        else:
            if self.ante >= MAX_ANTE:
                self.phase = "victory"
                return
            self.ante += 1
            self.blinds = make_blinds(self.ante)
            self.blind_index = 0
        self._start_blind_round()

    def is_run_over(self):
        return self.phase in ("game_over", "victory")
