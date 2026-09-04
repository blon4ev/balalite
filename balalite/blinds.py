import dataclasses
from dataclasses import dataclass, field
from typing import FrozenSet, Optional

from .cards import Rank, Suit
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
    debuff_ranks: FrozenSet[Rank] = field(default_factory=frozenset)
    banned_hand_types: FrozenSet[HandType] = field(default_factory=frozenset)
    max_cards_per_play: Optional[int] = None
    joker_mult_scale: float = 1.0


_FACE_RANKS = frozenset({Rank.JACK, Rank.QUEEN, Rank.KING})
_EVEN_RANKS = frozenset(r for r in Rank if r.order % 2 == 0)
_ODD_RANKS = frozenset(r for r in Rank if r.order % 2 == 1)

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
    BossEffect("검은 모래", "♠ 스페이드 카드는 칩 점수에 기여하지 않습니다.", debuff_suit=Suit.SPADES),
    BossEffect("차가운 유리", "♦ 다이아몬드 카드는 칩 점수에 기여하지 않습니다.", debuff_suit=Suit.DIAMONDS),
    BossEffect(
        "굳은 손가락", "한 번에 최대 2장까지만 낼 수 있습니다.", max_cards_per_play=2,
    ),
    BossEffect(
        "졸린 오후", "한 번에 최대 3장까지만 낼 수 있습니다.", max_cards_per_play=3,
    ),
    BossEffect(
        "그림자 재판관", "트리플과 포카드는 무효 처리(0점)됩니다.",
        banned_hand_types=frozenset({HandType.THREE_OF_A_KIND, HandType.FOUR_OF_A_KIND}),
    ),
    BossEffect(
        "메아리 없는 방", "조커로 얻는 배수 보너스가 절반만 적용됩니다.", joker_mult_scale=0.5,
    ),
    BossEffect(
        "속삭이는 안개", "조커로 얻는 배수 보너스가 30%만 적용됩니다.", joker_mult_scale=0.3,
    ),
    BossEffect(
        "얼굴 없는 왕국", "그림카드(J/Q/K)는 칩 점수에 기여하지 않습니다.", debuff_ranks=_FACE_RANKS,
    ),
    BossEffect(
        "짝수의 저주", "짝수 카드(2/4/6/8/10/Q)는 칩 점수에 기여하지 않습니다.", debuff_ranks=_EVEN_RANKS,
    ),
    BossEffect(
        "홀수의 저주", "홀수 카드(3/5/7/9/J/K/A)는 칩 점수에 기여하지 않습니다.", debuff_ranks=_ODD_RANKS,
    ),
]


def _intensify(effect):
    """스테이크 최고 단계에서 보스 효과를 한 단계 더 가혹하게 만든다.
    이미 0인 항목은 건드리지 않고, 값이 있는 항목만 조금 더 강하게 조정한다."""
    changes = {}
    if effect.hand_size_delta < 0:
        changes["hand_size_delta"] = effect.hand_size_delta - 1
    if effect.plays_delta < 0:
        changes["plays_delta"] = effect.plays_delta - 1
    if 0 > effect.discards_delta > -50:
        changes["discards_delta"] = effect.discards_delta - 1
    if effect.money_tax > 0:
        changes["money_tax"] = effect.money_tax + 5
    if effect.max_cards_per_play is not None:
        changes["max_cards_per_play"] = max(1, effect.max_cards_per_play - 1)
    if effect.joker_mult_scale < 1.0:
        changes["joker_mult_scale"] = max(0.0, effect.joker_mult_scale - 0.2)
    if not changes:
        return effect
    return dataclasses.replace(effect, **changes)


@dataclass
class Blind:
    kind: str  # "small" | "big" | "boss"
    label: str
    requirement: int
    boss_effect: Optional[BossEffect] = None


def make_blinds(ante, requirement_multiplier=1.0, intensify_boss=False):
    base = 300 * (1.6 ** (ante - 1)) * requirement_multiplier
    small = int(round(base / 10) * 10)
    big = int(round(base * 1.5 / 10) * 10)
    boss = int(round(base * 2 / 10) * 10)
    boss_effect = BOSS_EFFECTS[(ante - 1) % len(BOSS_EFFECTS)]
    if intensify_boss:
        boss_effect = _intensify(boss_effect)
    return [
        Blind("small", "스몰 블라인드", small),
        Blind("big", "빅 블라인드", big),
        Blind("boss", f"보스 블라인드 · {boss_effect.name}", boss, boss_effect),
    ]
