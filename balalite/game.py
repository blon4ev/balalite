import random

from .blinds import MAX_ANTE, make_blinds
from .cards import Deck
from .jokers import JOKER_POOL, apply_jokers
from .scoring import evaluate_hand

HAND_SIZE = 8
PLAYS_PER_ROUND = 4
DISCARDS_PER_ROUND = 3
STARTING_MONEY = 4
MAX_JOKER_SLOTS = 5
SHOP_OFFER_COUNT = 3


class GameState:
    def __init__(self):
        self.deck = Deck()
        self.ante = 1
        self.blinds = make_blinds(self.ante)
        self.blind_index = 0
        self.money = STARTING_MONEY
        self.jokers = []
        self.hand = []
        self.round_score = 0
        self.plays_left = PLAYS_PER_ROUND
        self.discards_left = DISCARDS_PER_ROUND
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

    def _start_blind_round(self):
        self.deck.reset()
        self.hand = self.deck.draw(HAND_SIZE)
        self.sort_hand(self.sort_mode)
        self.round_score = 0
        self.plays_left = PLAYS_PER_ROUND
        self.discards_left = DISCARDS_PER_ROUND
        self.phase = "blind"
        self.last_result = None

    def sort_hand(self, by="rank"):
        self.sort_mode = by
        if by == "rank":
            self.hand.sort(key=lambda c: c.rank.order, reverse=True)
        else:
            self.hand.sort(key=lambda c: (c.suit.name, -c.rank.order))

    def play_cards(self, indices):
        cards = [self.hand[i] for i in indices]
        hand_type, scoring_cards = evaluate_hand(cards)
        base_chips = hand_type.base_chips + sum(c.rank.chips for c in scoring_cards)
        base_mult = hand_type.base_mult
        chips, mult = apply_jokers(self.jokers, cards, scoring_cards, hand_type, base_chips, base_mult)
        gained = int(chips * mult)
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
        k = min(SHOP_OFFER_COUNT, len(JOKER_POOL))
        self.shop_offers = random.sample(JOKER_POOL, k=k)

    def buy_joker(self, offer_index):
        if offer_index < 0 or offer_index >= len(self.shop_offers):
            self.shop_message = "잘못된 번호입니다."
            return
        joker = self.shop_offers[offer_index]
        if len(self.jokers) >= MAX_JOKER_SLOTS:
            self.shop_message = "조커 슬롯이 가득 찼습니다."
            return
        if self.money < joker.cost:
            self.shop_message = "돈이 부족합니다."
            return
        self.money -= joker.cost
        self.jokers.append(joker)
        del self.shop_offers[offer_index]
        self.shop_message = f"'{joker.name}' 구매 완료!"

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
