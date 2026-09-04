from dataclasses import dataclass
from typing import Callable, List


@dataclass(frozen=True)
class Voucher:
    key: str
    name: str
    description: str
    cost: int
    kind: str = "voucher"
    effect: Callable[["GameState"], None] = None


def _extend_hand(game):
    game.base_hand_size += 1


def _extend_discards(game):
    game.base_discards += 1


def _extend_plays(game):
    game.base_plays += 1


def _shop_discount(game):
    game.shop_discount = min(0.5, game.shop_discount + 0.2)


def _interest_boost(game):
    game.interest_cap += 5


def _shop_expansion(game):
    game.shop_offer_count += 1


def _joker_slot_expansion(game):
    game.max_joker_slots += 1


def _consumable_slot_expansion(game):
    game.max_consumable_slots += 1


VOUCHER_POOL: List[Voucher] = [
    Voucher("voucher_hand", "확장 훈련", "카드 패 크기가 영구히 1장 늘어납니다.", 10, effect=_extend_hand),
    Voucher("voucher_discard", "여유 훈련", "웨이브당 재정비 횟수가 영구히 1회 늘어납니다.", 10, effect=_extend_discards),
    Voucher("voucher_play", "숙련 훈련", "웨이브당 공격 횟수가 영구히 1회 늘어납니다.", 12, effect=_extend_plays),
    Voucher("voucher_discount", "협상 훈련", "보급소 구매 가격이 20% 할인됩니다 (중첩 가능, 최대 50%).", 10, effect=_shop_discount),
    Voucher("voucher_interest", "저축 훈련", "이자 상한이 $5 늘어납니다.", 8, effect=_interest_boost),
    Voucher("voucher_shop", "안목 훈련", "보급소 카드 슬롯(유물·보급품) 수가 1개 늘어납니다.", 10, effect=_shop_expansion),
    Voucher("voucher_joker_slot", "장비창 훈련", "유물 슬롯이 영구히 1개 늘어납니다.", 14, effect=_joker_slot_expansion),
    Voucher("voucher_consumable_slot", "배낭 훈련", "보급품 슬롯이 영구히 1개 늘어납니다.", 12, effect=_consumable_slot_expansion),
]
