import dataclasses
import random

from .blinds import MAX_ANTE, make_blinds
from .cards import Deck, card_from_dict, card_to_dict
from .consumables import CARD_MODIFIER_POOL, CONSUMABLE_POOL, ENHANCEMENT_DESCRIPTIONS, LEVEL_BONUS
from .decks import deck_by_key
from .jokers import JOKER_POOL, RARITY_WEIGHT, apply_jokers
from .packs import PACK_POOL
from .scoring import HandType, evaluate_hand
from .stakes import STAKE_POOL, stake_by_level
from .tags import TAG_POOL
from .vouchers import VOUCHER_POOL

HAND_SIZE = 8
PLAYS_PER_ROUND = 4
DISCARDS_PER_ROUND = 3
STARTING_MONEY = 4
MAX_JOKER_SLOTS = 5
MAX_CONSUMABLE_SLOTS = 2
SHOP_CARD_SLOTS = 2  # 조커·소모품이 나오는 카드 슬롯 수 (바우처로 증가 가능)
SHOP_PACK_SLOTS = 2  # 부스터 팩 전용 슬롯 수 (고정)
SHOP_REROLL_COST = 2
REROLL_COST_INCREMENT = 1  # 같은 상점 방문에서 리롤할 때마다 비용이 이만큼씩 오름
DEFAULT_INTEREST_CAP = 5
GLASS_BREAK_CHANCE = 0.25
GOLD_SEAL_INCOME = 3
CONSUMABLE_SHOP_WEIGHT = 5
# 3단계 이상 스테이크에서 블라인드 목표 점수에 곱해지는 배율
STAKE_BLIND_MULTIPLIER = 1.10


def _weighted_unique_sample(rng, items, weights, k):
    remaining = list(zip(items, weights))
    chosen = []
    for _ in range(min(k, len(remaining))):
        total = sum(w for _, w in remaining)
        r = rng.uniform(0, total)
        upto = 0.0
        for i, (item, w) in enumerate(remaining):
            upto += w
            if upto >= r:
                chosen.append(item)
                del remaining[i]
                break
    return chosen


def _joker_by_key(key):
    return next(j for j in JOKER_POOL if j.key == key)


def _consumable_by_key(key):
    return next(c for c in CONSUMABLE_POOL if c.key == key)


def _voucher_by_key(key):
    return next(v for v in VOUCHER_POOL if v.key == key)


def _pack_by_key(key):
    return next(p for p in PACK_POOL if p.key == key)


def _offer_to_dict(item):
    if hasattr(item, "timing"):
        return {"type": "joker", "key": item.key}
    kind = getattr(item, "kind", None)
    if kind == "voucher":
        return {"type": "voucher", "key": item.key}
    if kind == "pack":
        return {"type": "pack", "key": item.key}
    return {"type": "consumable", "key": item.key}


def _offer_from_dict(data):
    kind = data["type"]
    if kind == "joker":
        return _joker_by_key(data["key"])
    if kind == "voucher":
        return _voucher_by_key(data["key"])
    if kind == "pack":
        return _pack_by_key(data["key"])
    return _consumable_by_key(data["key"])


class GameState:
    def __init__(self, seed=None, deck_key="deck_standard", stake_level=1):
        self.rng = random.Random(seed)
        self.seed = seed

        deck_type = deck_by_key(deck_key)
        stake = stake_by_level(max(1, min(len(STAKE_POOL), stake_level)))
        self.deck_key = deck_type.key
        self.stake_level = stake.level
        self.intensify_boss = self.stake_level >= 5

        self.deck = Deck(self.rng)
        if deck_type.pre_enhanced_card_count:
            sample = self.rng.sample(
                self.deck.cards, min(deck_type.pre_enhanced_card_count, len(self.deck.cards))
            )
            for c in sample:
                c.enhancement = self.rng.choice(list(ENHANCEMENT_DESCRIPTIONS.keys()))

        self.blind_requirement_multiplier = deck_type.blind_requirement_multiplier * (
            STAKE_BLIND_MULTIPLIER if self.stake_level >= 3 else 1.0
        )
        self.ante = 1
        self.blinds = make_blinds(self.ante, self.blind_requirement_multiplier, self.intensify_boss)
        self.blind_index = 0
        self.money = max(0, STARTING_MONEY + deck_type.money_delta)
        self.jokers = []
        if deck_type.starting_joker_rarity:
            candidates = [j for j in JOKER_POOL if j.rarity == deck_type.starting_joker_rarity]
            if candidates:
                self.jokers.append(self.rng.choice(candidates))
        self.consumables = []
        self.hand_levels = {}
        self.owned_vouchers = set()

        self.base_hand_size = max(1, HAND_SIZE + deck_type.hand_size_delta)
        self.base_plays = PLAYS_PER_ROUND
        self.base_discards = max(0, DISCARDS_PER_ROUND - (1 if self.stake_level >= 4 else 0))
        self.max_joker_slots = max(
            1, MAX_JOKER_SLOTS + deck_type.joker_slot_delta - (1 if self.stake_level >= 5 else 0)
        )
        self.max_consumable_slots = max(0, MAX_CONSUMABLE_SLOTS + deck_type.consumable_slot_delta)
        self.shop_offer_count = SHOP_CARD_SLOTS
        self.shop_discount = 0.0
        self.interest_cap = DEFAULT_INTEREST_CAP
        self.base_reroll_cost = max(1, SHOP_REROLL_COST + deck_type.reroll_cost_delta)
        self.reroll_cost = self.base_reroll_cost

        self.hand = []
        self.hand_size = HAND_SIZE
        self.round_score = 0
        self.plays_left = PLAYS_PER_ROUND
        self.discards_left = DISCARDS_PER_ROUND
        self.next_play_mult_multiplier = 1
        self.mist_active = False
        self.echo_mult_bonus = 0
        self._round_started_fresh = True

        self.phase = "blind"
        self.last_result = None
        self.last_reward = 0
        self.last_interest = 0
        self.last_tag_message = None
        self.sort_mode = "rank"
        self.shop_offers = []
        self.shop_message = ""
        self.pending_pack = None
        self._start_blind_round()

    @property
    def current_blind(self):
        return self.blinds[self.blind_index]

    @property
    def boss_effect(self):
        return self.current_blind.boss_effect

    def joker_slot_count(self):
        """네거티브 에디션 조커는 슬롯을 차지하지 않는다."""
        return sum(1 for j in self.jokers if j.edition != "negative")

    def consumable_slot_count(self):
        """네거티브 에디션 소모품은 슬롯을 차지하지 않는다."""
        return sum(1 for c in self.consumables if c.edition != "negative")

    def _start_blind_round(self):
        self.deck.reshuffle_round(self.hand)
        self.hand = []
        self.hand_size = self.base_hand_size
        self.plays_left = self.base_plays
        self.discards_left = self.base_discards
        self.next_play_mult_multiplier = 1
        self.mist_active = False
        self.echo_mult_bonus = 0

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
            card_chip = 0
            card_mult_add = 0
            card_mult_mul = 1.0
            debuffed = effect and (
                (effect.debuff_suit and c.suit is effect.debuff_suit)
                or (effect.debuff_ranks and c.rank in effect.debuff_ranks)
            )
            if not debuffed:
                card_chip += c.rank.chips
            if c.enhancement == "bonus":
                card_chip += 30
            elif c.enhancement == "mult":
                card_mult_add += 4
            elif c.enhancement == "glass":
                card_mult_mul *= 2
                if self.rng.random() < GLASS_BREAK_CHANCE:
                    destroyed.append(c)
            if c.edition == "foil":
                card_chip += 50
            elif c.edition == "holographic":
                card_mult_add += 10
            elif c.edition == "polychrome":
                card_mult_mul *= 1.5

            if c.seal == "red":
                card_chip *= 2
                card_mult_add *= 2
                card_mult_mul *= card_mult_mul

            chip_sum += card_chip
            mult_bonus += card_mult_add
            mult_multiplier *= card_mult_mul

        gold_income = sum(GOLD_SEAL_INCOME for c in cards if c.seal == "gold")
        if gold_income:
            self.money += gold_income

        base_chips = hand_type.base_chips + level * level_chips + chip_sum
        base_mult = hand_type.base_mult + level * level_mult + mult_bonus
        chips, mult = apply_jokers(self.jokers, cards, scoring_cards, hand_type, base_chips, base_mult, game=self)

        if effect and effect.joker_mult_scale != 1.0:
            mult = base_mult + (mult - base_mult) * effect.joker_mult_scale

        if self.mist_active:
            chips = base_chips + (chips - base_chips) * 2
            mult = base_mult + (mult - base_mult) * 2
            self.mist_active = False

        mult += self.echo_mult_bonus
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
        for c in cards:
            if c.seal == "blue" and self.consumable_slot_count() < self.max_consumable_slots:
                self.consumables.append(self.rng.choice(CONSUMABLE_POOL))
        self.hand.extend(self.deck.draw(len(indices)))
        self.sort_hand(self.sort_mode)
        self.discards_left -= 1
        self._round_started_fresh = False
        self.last_result = None

    def use_consumable(self, index, target_index=None):
        if index < 0 or index >= len(self.consumables):
            return "잘못된 번호입니다."
        item = self.consumables[index]
        target = None
        if item.target_type == "card":
            if target_index is None or not (0 <= target_index < len(self.hand)):
                return "대상 카드 번호를 올바르게 지정하세요 (예: u 1 3)."
            target = self.hand[target_index]
        elif item.target_type == "joker":
            if target_index is None or not (0 <= target_index < len(self.jokers)):
                return "대상 조커 번호를 올바르게 지정하세요 (예: u 1 2, j로 번호 확인)."
            target = self.jokers[target_index]
        elif item.target_type == "consumable":
            if (
                target_index is None
                or not (0 <= target_index < len(self.consumables))
                or target_index == index
            ):
                return "대상 소모품 번호를 올바르게 지정하세요 (자기 자신은 지정할 수 없습니다)."
            target = self.consumables[target_index]

        self.consumables.pop(index)
        item.effect(self, target)
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
            if self.stake_level >= 2 and self.current_blind.kind == "small":
                self.last_reward = 0
            else:
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
        self.reroll_cost = self.base_reroll_cost
        self._roll_shop_offers()

    def _roll_shop_offers(self):
        """실제 발라트로처럼 상점 슬롯을 영역별로 나눠서 굴린다:
        카드 슬롯(조커 또는 소모품, 바우처로 개수 증가 가능) + 부스터 팩 전용 슬롯(고정 2개)
        + 미보유 바우처 슬롯(있으면 1개). 팩은 카드 슬롯과 경쟁하지 않고 항상 등장한다."""
        card_pool = list(JOKER_POOL) + list(CONSUMABLE_POOL)
        card_weights = (
            [RARITY_WEIGHT[j.rarity] for j in JOKER_POOL]
            + [CONSUMABLE_SHOP_WEIGHT] * len(CONSUMABLE_POOL)
        )
        card_slots = min(self.shop_offer_count, len(card_pool))
        self.shop_offers = _weighted_unique_sample(self.rng, card_pool, card_weights, card_slots)

        if not any(offer in CARD_MODIFIER_POOL for offer in self.shop_offers):
            guaranteed = self.rng.choice(CARD_MODIFIER_POOL)
            replace_idx = next(
                (
                    i
                    for i, offer in enumerate(self.shop_offers)
                    if offer in CONSUMABLE_POOL and offer not in CARD_MODIFIER_POOL
                ),
                None,
            )
            if replace_idx is not None:
                self.shop_offers[replace_idx] = guaranteed
            else:
                self.shop_offers.append(guaranteed)

        pack_slots = min(SHOP_PACK_SLOTS, len(PACK_POOL))
        self.shop_offers += _weighted_unique_sample(
            self.rng, PACK_POOL, [1] * len(PACK_POOL), pack_slots
        )

        voucher_candidates = [v for v in VOUCHER_POOL if v.key not in self.owned_vouchers]
        if voucher_candidates:
            self.shop_offers.append(self.rng.choice(voucher_candidates))

    def reroll_shop(self):
        if self.money < self.reroll_cost:
            self.shop_message = "돈이 부족합니다."
            return
        self.money -= self.reroll_cost
        self.reroll_cost += REROLL_COST_INCREMENT
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

        if kind == "pack":
            if self.money < cost:
                self.shop_message = "돈이 부족합니다."
                return
            self.money -= cost
            del self.shop_offers[offer_index]
            self._open_pack(item)
            return

        is_joker = hasattr(item, "timing")
        if is_joker and self.joker_slot_count() >= self.max_joker_slots:
            self.shop_message = "조커 슬롯이 가득 찼습니다."
            return
        if not is_joker and self.consumable_slot_count() >= self.max_consumable_slots:
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

    def _open_pack(self, pack):
        if pack.pack_type == "joker":
            source_pool = JOKER_POOL
            weights = [RARITY_WEIGHT[j.rarity] for j in source_pool]
        else:
            source_pool = CONSUMABLE_POOL
            weights = [1] * len(source_pool)
        items = _weighted_unique_sample(self.rng, source_pool, weights, pack.show_count)
        self.pending_pack = {
            "pack_type": pack.pack_type,
            "items": items,
            "remaining": pack.pick_count,
        }
        self.phase = "pack"
        self.shop_message = ""

    def pick_pack_item(self, index):
        if self.phase != "pack" or not self.pending_pack:
            return "지금은 선택할 수 없습니다."
        items = self.pending_pack["items"]
        if index < 0 or index >= len(items):
            return "잘못된 번호입니다."
        item = items[index]
        pack_type = self.pending_pack["pack_type"]
        if pack_type == "joker" and self.joker_slot_count() >= self.max_joker_slots:
            return "조커 슬롯이 가득 찼습니다."
        if pack_type == "consumable" and self.consumable_slot_count() >= self.max_consumable_slots:
            return "소모품 슬롯이 가득 찼습니다."

        del items[index]
        if pack_type == "joker":
            self.jokers.append(item)
        else:
            self.consumables.append(item)
        self.pending_pack["remaining"] -= 1
        message = f"'{item.name}' 획득!"
        if self.pending_pack["remaining"] <= 0 or not items:
            self.phase = "shop"
            self.pending_pack = None
        return message

    def skip_pack(self):
        if self.phase != "pack":
            return "지금은 스킵할 수 없습니다."
        self.phase = "shop"
        self.pending_pack = None
        return "나머지 선택을 건너뛰었습니다."

    def continue_from_shop(self):
        if self.blind_index + 1 < len(self.blinds):
            self.blind_index += 1
        else:
            if self.ante >= MAX_ANTE:
                self.phase = "victory"
                return
            self.ante += 1
            self.blinds = make_blinds(self.ante, self.blind_requirement_multiplier, self.intensify_boss)
            self.blind_index = 0
        self._start_blind_round()

    def is_run_over(self):
        return self.phase in ("game_over", "victory")

    def to_dict(self):
        version, internal_state, gauss_next = self.rng.getstate()
        return {
            "seed": self.seed,
            "deck_key": self.deck_key,
            "stake_level": self.stake_level,
            "max_joker_slots": self.max_joker_slots,
            "max_consumable_slots": self.max_consumable_slots,
            "reroll_cost": self.reroll_cost,
            "rng_state": [version, list(internal_state), gauss_next],
            "ante": self.ante,
            "blind_index": self.blind_index,
            "money": self.money,
            "jokers": [{"key": j.key, "edition": j.edition} for j in self.jokers],
            "consumables": [{"key": c.key, "edition": c.edition} for c in self.consumables],
            "hand_levels": {ht.name: lv for ht, lv in self.hand_levels.items()},
            "owned_vouchers": list(self.owned_vouchers),
            "base_hand_size": self.base_hand_size,
            "base_plays": self.base_plays,
            "base_discards": self.base_discards,
            "shop_offer_count": self.shop_offer_count,
            "shop_discount": self.shop_discount,
            "interest_cap": self.interest_cap,
            "hand": [card_to_dict(c) for c in self.hand],
            "hand_size": self.hand_size,
            "round_score": self.round_score,
            "plays_left": self.plays_left,
            "discards_left": self.discards_left,
            "next_play_mult_multiplier": self.next_play_mult_multiplier,
            "mist_active": self.mist_active,
            "echo_mult_bonus": self.echo_mult_bonus,
            "phase": self.phase,
            "last_reward": self.last_reward,
            "last_interest": self.last_interest,
            "sort_mode": self.sort_mode,
            "deck_cards": [card_to_dict(c) for c in self.deck.cards],
            "deck_discard_pile": [card_to_dict(c) for c in self.deck.discard_pile],
            "shop_offers": [_offer_to_dict(item) for item in self.shop_offers],
            "shop_message": self.shop_message,
        }

    @classmethod
    def from_dict(cls, data):
        game = cls.__new__(cls)
        version, internal_state, gauss_next = data["rng_state"]
        game.rng = random.Random()
        game.rng.setstate((version, tuple(internal_state), gauss_next))
        game.seed = data["seed"]
        game.deck_key = data.get("deck_key", "deck_standard")
        game.stake_level = data.get("stake_level", 1)
        deck_type = deck_by_key(game.deck_key)
        game.blind_requirement_multiplier = deck_type.blind_requirement_multiplier * (
            STAKE_BLIND_MULTIPLIER if game.stake_level >= 3 else 1.0
        )
        game.intensify_boss = game.stake_level >= 5
        game.base_reroll_cost = max(1, SHOP_REROLL_COST + deck_type.reroll_cost_delta)
        game.max_joker_slots = data.get("max_joker_slots", MAX_JOKER_SLOTS)
        game.max_consumable_slots = data.get("max_consumable_slots", MAX_CONSUMABLE_SLOTS)
        game.reroll_cost = data.get("reroll_cost", game.base_reroll_cost)
        game.deck = Deck(game.rng)
        game.deck.cards = [card_from_dict(d) for d in data["deck_cards"]]
        game.deck.discard_pile = [card_from_dict(d) for d in data["deck_discard_pile"]]
        game.ante = data["ante"]
        game.blinds = make_blinds(game.ante, game.blind_requirement_multiplier, game.intensify_boss)
        game.blind_index = data["blind_index"]
        game.money = data["money"]
        game.jokers = [
            dataclasses.replace(_joker_by_key(d["key"]), edition=d.get("edition"))
            for d in data["jokers"]
        ]
        game.consumables = [
            dataclasses.replace(_consumable_by_key(d["key"]), edition=d.get("edition"))
            for d in data["consumables"]
        ]
        game.hand_levels = {HandType[name]: lv for name, lv in data["hand_levels"].items()}
        game.owned_vouchers = set(data["owned_vouchers"])
        game.base_hand_size = data["base_hand_size"]
        game.base_plays = data["base_plays"]
        game.base_discards = data["base_discards"]
        game.shop_offer_count = data["shop_offer_count"]
        game.shop_discount = data["shop_discount"]
        game.interest_cap = data["interest_cap"]
        game.hand = [card_from_dict(d) for d in data["hand"]]
        game.hand_size = data["hand_size"]
        game.round_score = data["round_score"]
        game.plays_left = data["plays_left"]
        game.discards_left = data["discards_left"]
        game.next_play_mult_multiplier = data["next_play_mult_multiplier"]
        game.mist_active = data["mist_active"]
        game.echo_mult_bonus = data["echo_mult_bonus"]
        game._round_started_fresh = False
        game.phase = data["phase"]
        game.last_result = None
        game.last_reward = data["last_reward"]
        game.last_interest = data["last_interest"]
        game.last_tag_message = None
        game.sort_mode = data["sort_mode"]
        game.shop_offers = [_offer_from_dict(d) for d in data["shop_offers"]]
        game.shop_message = data["shop_message"]
        game.pending_pack = None
        return game
