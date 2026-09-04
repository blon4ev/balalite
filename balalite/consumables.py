from dataclasses import dataclass
from typing import Callable, List, Optional

from .scoring import HandType

# 족보 레벨당 (칩 보너스, 배수 보너스). 발라트로의 "행성 카드"에 해당하는 시스템으로,
# 표준 9족보 + 와일드 강화로만 달성 가능한 히든 3족보까지 총 12종을 커버한다.
LEVEL_BONUS = {
    HandType.HIGH_CARD: (5, 1),
    HandType.PAIR: (10, 1),
    HandType.TWO_PAIR: (15, 1),
    HandType.THREE_OF_A_KIND: (20, 2),
    HandType.STRAIGHT: (25, 2),
    HandType.FLUSH: (20, 2),
    HandType.FULL_HOUSE: (25, 2),
    HandType.FOUR_OF_A_KIND: (30, 3),
    HandType.STRAIGHT_FLUSH: (40, 4),
    HandType.FIVE_OF_A_KIND: (35, 4),
    HandType.FLUSH_HOUSE: (40, 5),
    HandType.FLUSH_FIVE: (50, 6),
}

# 카드 강화 종류와 설명 (게임플레이 로직은 game.py의 _score_cards와 scoring.py에서 처리)
ENHANCEMENT_DESCRIPTIONS = {
    "bonus": "이 카드가 점수에 포함되면 +30 칩",
    "mult": "이 카드가 점수에 포함되면 +4 Mult",
    "wild": "플러시 판정 시 모든 무늬로 취급되며, 나머지 카드가 전부 같은 랭크면 파이브 오브 어 카인드 등 히든 조합의 마지막 한 장을 채워줌",
    "glass": "이 카드가 점수에 포함되면 Mult x2, 이후 25% 확률로 파괴됨",
}

# 카드 에디션 종류와 설명 (강화와 별개로 부여 가능, game.py의 _score_cards에서 처리)
EDITION_DESCRIPTIONS = {
    "foil": "이 카드가 점수에 포함되면 +50 칩",
    "holographic": "이 카드가 점수에 포함되면 +10 Mult",
    "polychrome": "이 카드가 점수에 포함되면 Mult x1.5",
}

# 카드 씰 종류와 설명 (강화/에디션과 별개인 세 번째 슬롯, game.py에서 처리)
SEAL_DESCRIPTIONS = {
    "red": "이 카드가 점수에 포함되면 강화·에디션 효과가 한 번 더(레트리거) 적용됨",
    "gold": "이 카드를 플레이할 때마다 즉시 +$3",
    "blue": "이 카드를 버리면 무작위 소모품 1개를 무료로 획득 (슬롯 여유 시)",
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

def _make_editioner_effect(edition):
    def effect(game, card=None):
        card.edition = edition
    return effect


EDITIONERS: List[Consumable] = [
    Consumable(
        f"editioner_{key}",
        f"{label} 에디션석",
        f"손패 카드 1장에 에디션을 부여합니다 — {EDITION_DESCRIPTIONS[key]}",
        9,
        "editioner",
        _make_editioner_effect(key),
        needs_target=True,
    )
    for key, label in [("foil", "포일"), ("holographic", "홀로그래픽"), ("polychrome", "폴리크롬")]
]


def _mist_spectral(game, card=None):
    game.mist_active = True


def _echo_spectral(game, card=None):
    game.echo_mult_bonus += 2


def _curse_spectral(game, card=None):
    if game.hand:
        target = game.rng.choice(game.hand)
        target.enhancement = game.rng.choice(list(ENHANCEMENT_DESCRIPTIONS.keys()))


def _ruin_spectral(game, card=None):
    if card in game.hand:
        game.hand.remove(card)
        game.hand.extend(game.deck.draw(1))
        game.sort_hand(game.sort_mode)


def _fortune_spectral(game, card=None):
    game.money += 15


def _clone_spectral(game, card=None):
    from .game import MAX_JOKER_SLOTS

    if game.jokers and len(game.jokers) < MAX_JOKER_SLOTS:
        game.jokers.append(game.rng.choice(game.jokers))
    else:
        game.money += 10


SPECTRALS: List[Consumable] = [
    Consumable(
        "spectral_mist", "안개", "이번 플레이에서 조커로 인한 추가 칩/배수 효과가 2배로 적용됩니다.",
        8, "spectral", _mist_spectral,
    ),
    Consumable(
        "spectral_echo", "메아리", "이번 라운드 남은 모든 플레이에 +2 Mult가 누적 적용됩니다.",
        7, "spectral", _echo_spectral,
    ),
    Consumable(
        "spectral_curse", "저주", "손패의 무작위 카드 1장에 무작위 강화를 부여합니다.",
        6, "spectral", _curse_spectral,
    ),
    Consumable(
        "spectral_ruin", "파괴", "지정한 손패 카드 1장을 덱에서 영구히 파괴합니다.",
        6, "spectral", _ruin_spectral, needs_target=True,
    ),
    Consumable(
        "spectral_fortune", "행운", "즉시 $15을 얻습니다.",
        9, "spectral", _fortune_spectral,
    ),
    Consumable(
        "spectral_clone", "복제", "보유한 조커 중 하나를 무작위로 복제합니다 (슬롯이 없으면 대신 $10).",
        12, "spectral", _clone_spectral,
    ),
]

def _make_sealer_effect(seal):
    def effect(game, card=None):
        card.seal = seal
    return effect


SEALERS: List[Consumable] = [
    Consumable(
        f"sealer_{key}",
        f"{label} 인장석",
        f"손패 카드 1장에 씰을 부여합니다 — {SEAL_DESCRIPTIONS[key]}",
        8,
        "sealer",
        _make_sealer_effect(key),
        needs_target=True,
    )
    for key, label in [("red", "적색"), ("gold", "금색"), ("blue", "청색")]
]

CONSUMABLE_POOL: List[Consumable] = CHARMS + RUNES + ENHANCERS + EDITIONERS + SEALERS + SPECTRALS
