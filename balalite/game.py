import random

from .blinds import MAX_ANTE, make_blinds
from .cards import Deck
from .consumables import CONSUMABLE_POOL, LEVEL_BONUS
from .jokers import JOKER_POOL, apply_jokers
from .scoring import evaluate_hand
from .tags import TAG_POOL
from .vouchers import VOUCHER_POOL

HAND_SIZE = 8
PLAYS_PER_ROUND = 4
DISCARDS_PER_ROUND = 3
STARTING_MONEY = 4
MAX_JOKER_SLOTS = 5
MAX_CONSUMABLE_SLOTS = 2
SHOP_OFFER_COUNT = 4
SHOP_REROLL_COST = 2
DEFAULT_INTEREST_CAP = 5
GLASS_BREAK_CHANCE = 0.25


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
        self.owned_vouchers = set()

        self.base_hand_size = HAND_SIZE
        self.base_plays = PLAYS_PER_ROUND
        self.base_discards = DISCARDS_PER_ROUND
        self.shop_offer_count = SHOP_OFFER_COUNT
        self.shop_discount = 0.0
        self.interest_cap = DEFAULT_INTEREST_CAP

        self.hand = []
        self.hand_size = HAND_SIZE
        self.round_score = 0
        self.plays_left = PLAYS_PER_ROUND
        self.discards_left = DISCARDS_PER_ROUND
        self.next_play_mult_multiplier = 1
        self._round_started_fresh = True

        self.phase = "blind"
        self.last_result = None
        self.last_reward = 0
        self.last_interest = 0
        self.last_tag_message = None
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
        self.deck.reshuffle_round(self.hand)
        self.hand = []
        self.hand_size = self.base_hand_size
        self.plays_left = self.base_plays
        self.discards_left = self.base_discards
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
        self.last_tag_message = None
        self._round_started_fresh = True

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
        mult_bonus = 0
        mult_multiplier = 1.0
        destroyed = []
        for c in scoring_cards:
            if not (effect and effect.debuff_suit and c.suit is effect.debuff_suit):
                chip_sum += c.rank.chips
            if c.enhancement == "bonus":
                chip_sum += 30
            elif c.enhancement == "mult":
                mult_bonus += 4
            elif c.enhancement == "glass":
                mult_multiplier *= 2
                if self.rng.random() < GLASS_BREAK_CHANCE:
                    destroyed.append(c)

        base_chips = hand_type.base_chips + level * level_chips + chip_sum
        base_mult = hand_type.base_mult + level * level_mult + mult_bonus
        chips, mult = apply_jokers(self.jokers, cards, scoring_cards, hand_type, base_chips, base_mult)
        mult *= mult_multiplier
        mult *= self.next_play_mult_multiplier
        self.next_play_mult_multiplier = 1

        if effect and hand_type in effect.banned_hand_types:
            gained = 0
        else:
            gained = int(chips * mult)
        return hand_type, chips, mult, gained, destroyed

    def play_cards(self, indices):
        cards = [self.hand[i] for i in indices]
        hand_type, chips, mult, gained, destroyed = self._score_cards(cards)
        self.round_score += gained

        for i in sorted(indices, reverse=True):
            del self.hand[i]
        survivors = [c for c in cards if c not in destroyed]
        self.deck.discard(survivors)
        self.hand.extend(self.deck.draw(len(indices)))
        self.sort_hand(self.sort_mode)

        self.plays_left -= 1
        self._round_started_fresh = False
        self.last_result = (hand_type, chips, mult, gained, destroyed)
        self._check_round_progress()

    def discard_cards(self, indices):
        cards = [self.hand[i] for i in indices]
        for i in sorted(indices, reverse=True):
            del self.hand[i]
        self.deck.discard(cards)
        self.hand.extend(self.deck.draw(len(indices)))
        self.sort_hand(self.sort_mode)
        self.discards_left -= 1
        self._round_started_fresh = False
        self.last_result = None

    def use_consumable(self, index, card_index=None):
        if index < 0 or index >= len(self.consumables):
            return "잘못된 번호입니다."
        item = self.consumables[index]
        card = None
        if item.needs_target:
            if card_index is None or not (0 <= card_index < len(self.hand)):
                return "대상 카드 번호를 올바르게 지정하세요 (예: u 1 3)."
            card = self.hand[card_index]
        item = self.consumables.pop(index)
        item.effect(self, card)
        return f"'{item.name}' 사용 완료!"

    def sell_joker(self, index):
        if index < 0 or index >= len(self.jokers):
            return "잘못된 번호입니다."
        joker = self.jokers.pop(index)
        refund = joker.cost // 2
        self.money += refund
        return f"'{joker.name}' 판매 완료! (+${refund})"

    def can_skip_blind(self):
        return self.phase == "blind" and self.current_blind.kind != "boss" and self._round_started_fresh

    def skip_blind(self):
        if not self.can_skip_blind():
            return "지금은 블라인드를 스킵할 수 없습니다."
        tag = self.rng.choice(TAG_POOL)
        tag.effect(self)
        message = self.last_tag_message or f"'{tag.name}' 효과를 받았습니다."
        self.continue_from_shop()
        self.last_tag_message = message
        return message

    def _check_round_progress(self):
        if self.round_score >= self.current_blind.requirement:
            self.last_reward = 3 + self.discards_left
            self.money += self.last_reward
            self.last_interest = min(self.money // 5, self.interest_cap)
            self.money += self.last_interest
            self._enter_shop()
        elif self.plays_left <= 0:
            self.phase = "game_over"

    def _enter_shop(self):
        self.phase = "shop"
        self.shop_message = ""
        self._roll_shop_offers()

    def _roll_shop_offers(self):
        pool = list(JOKER_POOL) + list(CONSUMABLE_POOL)
        k = min(self.shop_offer_count, len(pool))
        self.shop_offers = self.rng.sample(pool, k=k)
        voucher_candidates = [v for v in VOUCHER_POOL if v.key not in self.owned_vouchers]
        if voucher_candidates:
            self.shop_offers.append(self.rng.choice(voucher_candidates))

    def reroll_shop(self):
        if self.money < SHOP_REROLL_COST:
            self.shop_message = "돈이 부족합니다."
            return
        self.money -= SHOP_REROLL_COST
        self._roll_shop_offers()
        self.shop_message = "상점을 새로고침했습니다."

    def _discounted_cost(self, cost):
        return max(1, int(cost * (1 - self.shop_discount)))

    def buy_offer(self, offer_index):
        if offer_index < 0 or offer_index >= len(self.shop_offers):
            self.shop_message = "잘못된 번호입니다."
            return
        item = self.shop_offers[offer_index]
        cost = self._discounted_cost(item.cost)
        kind = getattr(item, "kind", None)

        if kind == "voucher":
            if self.money < cost:
                self.shop_message = "돈이 부족합니다."
                return
            self.money -= cost
            item.effect(self)
            self.owned_vouchers.add(item.key)
            del self.shop_offers[offer_index]
            self.shop_message = f"'{item.name}' 획득 완료! (영구 효과)"
            return

        is_joker = hasattr(item, "timing")
        if is_joker and len(self.jokers) >= MAX_JOKER_SLOTS:
            self.shop_message = "조커 슬롯이 가득 찼습니다."
            return
        if not is_joker and len(self.consumables) >= MAX_CONSUMABLE_SLOTS:
            self.shop_message = "소모품 슬롯이 가득 찼습니다."
            return
        if self.money < cost:
            self.shop_message = "돈이 부족합니다."
            return

        self.money -= cost
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
