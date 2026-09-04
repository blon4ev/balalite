from dataclasses import dataclass
from typing import Callable, List, Optional

from .scoring import HandType

# 족보 레벨당 (칩 보너스, 배수 보너스). 하이 카드/스트레이트 플러시는 룬 대상에서 제외.
LEVEL_BONUS = {
    HandType.PAIR: (10, 1),
    HandType.TWO_PAIR: (15, 1),
    HandType.THREE_OF_A_KIND: (20, 2),
    HandType.STRAIGHT: (25, 2),
    HandType.FLUSH: (20, 2),
    HandType.FULL_HOUSE: (25, 2),
    HandType.FOUR_OF_A_KIND: (30, 3),
    HandType.STRAIGHT_FLUSH: (40, 4),
}

# 카드 강화 종류와 설명 (게임플레이 로직은 game.py의 _score_cards에서 처리)
ENHANCEMENT_DESCRIPTIONS = {
    "bonus": "이 카드가 점수에 포함되면 +30 칩",
    "mult": "이 카드가 점수에 포함되면 +4 Mult",
    "wild": "플러시 판정 시 모든 무늬로 취급",
    "glass": "이 카드가 점수에 포함되면 Mult x2, 이후 25% 확률로 파괴됨",
}


@dataclass(frozen=True)
class Consumable:
    key: str
    name: str
    description: str
    cost: int
    kind: str  # "charm" | "rune" | "enhancer"
    effect: Callable[["GameState", Optional["Card"]], None]
    hand_type: Optional[HandType] = None  # kind == "rune"일 때만 사용
    needs_target: bool = False  # kind == "enhancer"일 때 카드 지정 필요


def _gold_charm(game, card=None):
    game.money += 8


def _double_charm(game, card=None):
    game.next_play_mult_multiplier *= 2


def _reset_charm(game, card=None):
    count = len(game.hand)
    for i in sorted(range(count), reverse=True):
        del game.hand[i]
    game.hand.extend(game.deck.draw(count))
    game.sort_hand(game.sort_mode)


def _ease_charm(game, card=None):
    game.discards_left += 2


def _chance_charm(game, card=None):
    game.plays_left += 1


CHARMS: List[Consumable] = [
    Consumable("gold_charm", "금화 부적", "즉시 $8을 얻습니다.", 5, "charm", _gold_charm),
    Consumable("double_charm", "배가 부적", "다음 플레이 1회의 배수가 2배가 됩니다.", 6, "charm", _double_charm),
    Consumable("reset_charm", "재정비 부적", "버리기 소모 없이 손패를 전부 새로 뽑습니다.", 6, "charm", _reset_charm),
    Consumable("ease_charm", "여유 부적", "이번 라운드 버리기 횟수가 2회 늘어납니다.", 5, "charm", _ease_charm),
    Consumable("chance_charm", "기회 부적", "이번 라운드 플레이 횟수가 1회 늘어납니다.", 7, "charm", _chance_charm),
]


def _make_rune_effect(hand_type):
    def effect(game, card=None):
        game.hand_levels[hand_type] = game.hand_levels.get(hand_type, 0) + 1
    return effect


def _rune_cost(hand_type):
    return 5 + hand_type.base_mult // 2


RUNES: List[Consumable] = [
    Consumable(
        f"rune_{hand_type.name.lower()}",
        f"{hand_type.label}의 룬",
        f"{hand_type.label} 족보의 기본 점수가 영구히 강화됩니다.",
        _rune_cost(hand_type),
        "rune",
        _make_rune_effect(hand_type),
        hand_type=hand_type,
    )
    for hand_type in LEVEL_BONUS
]


def _make_enhancer_effect(enhancement):
    def effect(game, card=None):
        card.enhancement = enhancement
    return effect


ENHANCERS: List[Consumable] = [
    Consumable(
        f"enhancer_{key}",
        f"{label} 강화석",
        f"손패 카드 1장에 강화를 부여합니다 — {ENHANCEMENT_DESCRIPTIONS[key]}",
        7,
        "enhancer",
        _make_enhancer_effect(key),
        needs_target=True,
    )
    for key, label in [("bonus", "보너스"), ("mult", "멀티"), ("wild", "와일드"), ("glass", "유리")]
]

CONSUMABLE_POOL: List[Consumable] = CHARMS + RUNES + ENHANCERS
