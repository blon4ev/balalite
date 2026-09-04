from collections import defaultdict
from enum import Enum

from .cards import Rank


class HandType(Enum):
    HIGH_CARD = ("하이 카드", 5, 1)
    PAIR = ("페어", 10, 2)
    TWO_PAIR = ("투 페어", 20, 2)
    THREE_OF_A_KIND = ("트리플", 30, 3)
    STRAIGHT = ("스트레이트", 30, 4)
    FLUSH = ("플러시", 35, 4)
    FULL_HOUSE = ("풀 하우스", 40, 4)
    FOUR_OF_A_KIND = ("포카드", 60, 7)
    STRAIGHT_FLUSH = ("스트레이트 플러시", 100, 8)
    FIVE_OF_A_KIND = ("파이브 오브 어 카인드", 120, 10)
    FLUSH_HOUSE = ("플러시 하우스", 140, 12)
    FLUSH_FIVE = ("플러시 파이브", 160, 15)

    def __init__(self, label, base_chips, base_mult):
        self.label = label
        self.base_chips = base_chips
        self.base_mult = base_mult


def _detect_straight(cards):
    if len(cards) != 5:
        return None
    orders = sorted({c.rank.order for c in cards})
    if len(orders) != 5:
        return None
    if orders[-1] - orders[0] == 4:
        return sorted(cards, key=lambda c: c.rank.order)
    if orders == [2, 3, 4, 5, 14]:
        return sorted(cards, key=lambda c: 1 if c.rank is Rank.ACE else c.rank.order)
    return None


def _detect_wild_five_of_a_kind(cards):
    """표준 52장 덱에서는 한 랭크가 최대 4장(무늬 4종)뿐이라 파이브 오브 어 카인드가
    원래 불가능하다. '와일드' 강화 카드는 무늬뿐 아니라 랭크 매칭에도 자유롭게
    쓰일 수 있어, 나머지 카드가 전부 같은 랭크면 와일드 카드가 그 다섯 번째 자리를
    채워준다고 본다. 반환값: None | "five" | "flush_five"
    """
    if len(cards) != 5:
        return None
    real_cards = [c for c in cards if c.enhancement != "wild"]
    if not real_cards:
        return "flush_five"
    if len({c.rank for c in real_cards}) != 1:
        return None
    if len({c.suit for c in real_cards}) <= 1:
        return "flush_five"
    return "five"


def _is_flush_house(cards):
    """이미 성립한 풀 하우스(3+2)의 카드 5장이 전부 한 무늬(와일드 제외)면
    플러시 하우스로 취급한다. 랭크 쪽은 일반 풀 하우스 판정을 그대로 쓰므로
    와일드 카드의 도움이 필요 없다."""
    if len(cards) != 5:
        return False
    groups = defaultdict(list)
    for c in cards:
        groups[c.rank].append(c)
    if sorted(len(v) for v in groups.values()) != [2, 3]:
        return False
    non_wild_suits = {c.suit for c in cards if c.enhancement != "wild"}
    return len(non_wild_suits) <= 1


def evaluate_hand(cards):
    """1~5장의 선택 카드를 받아 (HandType, 점수에 포함되는 카드 목록)을 반환한다."""
    if not cards:
        raise ValueError("최소 한 장의 카드를 선택해야 합니다.")

    wild_kind = _detect_wild_five_of_a_kind(cards)
    if wild_kind == "flush_five":
        return HandType.FLUSH_FIVE, cards
    if _is_flush_house(cards):
        return HandType.FLUSH_HOUSE, cards
    if wild_kind == "five":
        return HandType.FIVE_OF_A_KIND, cards

    groups = defaultdict(list)
    for c in cards:
        groups[c.rank].append(c)
    counts = sorted(((len(v), k.order, k) for k, v in groups.items()), reverse=True)
    counts = [(cnt, rank) for cnt, _, rank in counts]

    non_wild_suits = {c.suit for c in cards if c.enhancement != "wild"}
    is_flush = len(cards) == 5 and len(non_wild_suits) <= 1
    straight_cards = _detect_straight(cards)

    if is_flush and straight_cards:
        return HandType.STRAIGHT_FLUSH, cards

    if counts[0][0] == 4:
        return HandType.FOUR_OF_A_KIND, groups[counts[0][1]]

    if len(cards) == 5 and counts[0][0] == 3 and len(counts) > 1 and counts[1][0] == 2:
        return HandType.FULL_HOUSE, cards

    if is_flush:
        return HandType.FLUSH, cards

    if straight_cards:
        return HandType.STRAIGHT, cards

    if counts[0][0] == 3:
        return HandType.THREE_OF_A_KIND, groups[counts[0][1]]

    pairs = [rank for cnt, rank in counts if cnt == 2]
    if len(pairs) >= 2:
        scoring = groups[pairs[0]] + groups[pairs[1]]
        return HandType.TWO_PAIR, scoring
    if len(pairs) == 1:
        return HandType.PAIR, groups[pairs[0]]

    best = max(cards, key=lambda c: c.rank.order)
    return HandType.HIGH_CARD, [best]
