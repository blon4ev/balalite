from dataclasses import dataclass, field
from typing import FrozenSet, Optional

from .cards import Suit
from .scoring import HandType

MAX_ANTE = 8


@dataclass(frozen=True)
class BossEffect:
    name: str
    description: str
    hand_size_delta: int = 0
    plays_delta: int = 0
    discards_delta: int = 0
    money_tax: int = 0
    debuff_suit: Optional[Suit] = None
    banned_hand_types: FrozenSet[HandType] = field(default_factory=frozenset)


BOSS_EFFECTS = [
    BossEffect("가위손", "손패가 2장 줄어든 6장으로 시작합니다.", hand_size_delta=-2),
    BossEffect("그림자 손님", "이 블라인드에서는 카드를 버릴 수 없습니다.", discards_delta=-99),
    BossEffect("얼어붙은 벽", "플레이 횟수가 1회 줄어듭니다.", plays_delta=-1),
    BossEffect("붉은 여왕", "♥ 하트 카드는 칩 점수에 기여하지 않습니다.", debuff_suit=Suit.HEARTS),
    BossEffect("미친 경매인", "블라인드 시작 시 $5를 징수당합니다.", money_tax=5),
    BossEffect(
        "냉혹한 심판", "하이 카드와 페어는 무효 처리(0점)됩니다.",
        banned_hand_types=frozenset({HandType.HIGH_CARD, HandType.PAIR}),
    ),
    BossEffect("황금 사슬", "♣ 클럽 카드는 칩 점수에 기여하지 않습니다.", debuff_suit=Suit.CLUBS),
    BossEffect(
        "폭풍의 눈", "스트레이트와 플러시는 무효 처리(0점)됩니다.",
        banned_hand_types=frozenset({HandType.STRAIGHT, HandType.FLUSH}),
    ),
]


@dataclass
class Blind:
    kind: str  # "small" | "big" | "boss"
    label: str
    requirement: int
    boss_effect: Optional[BossEffect] = None


def make_blinds(ante):
    base = 300 * (1.6 ** (ante - 1))
    small = int(round(base / 10) * 10)
    big = int(round(base * 1.5 / 10) * 10)
    boss = int(round(base * 2 / 10) * 10)
    boss_effect = BOSS_EFFECTS[(ante - 1) % len(BOSS_EFFECTS)]
    return [
        Blind("small", "스몰 블라인드", small),
        Blind("big", "빅 블라인드", big),
        Blind("boss", f"보스 블라인드 · {boss_effect.name}", boss, boss_effect),
    ]
