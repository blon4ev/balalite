import dataclasses
from dataclasses import dataclass, field
from typing import FrozenSet, Optional

from .cards import Rank, Suit
from .scoring import HandType

MAX_ANTE = 8

# 스테이지(옛 앤티)의 1차/2차 웨이브에 붙는 몬스터 무리 이름. 순수 표시용 플레이버라
# 게임 로직에는 영향이 없다 (스테이지 번호로 결정되는 고정 패턴, RNG 소비 없음).
SMALL_WAVE_FLAVOR = [
    "배회하는 감염체 무리", "긁힌 손톱 떼", "썩은 이빨 무리", "낮은 신음소리 떼",
    "절뚝이는 감염체 무리", "굶주린 무리", "안개 속 그림자 떼", "무너진 방벽의 잔당",
]
BIG_WAVE_FLAVOR = [
    "변종 감염체 무리", "돌연변이 떼", "폭주한 무리", "포효하는 감염체 집단",
    "핏빛 눈의 무리", "거대화한 변종 떼", "칠흑의 무리", "최후의 방어선을 뚫은 무리",
]


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

# 보스 웨이브 몬스터 특성. 이름은 그대로 보스 몬스터의 별명으로 쓴다.
BOSS_EFFECTS = [
    BossEffect("가위손", "휘두르는 손톱에 카드 2장을 베여 6장으로 시작합니다.", hand_size_delta=-2),
    BossEffect("그림자 손님", "이 웨이브에서는 카드를 버릴 수 없습니다.", discards_delta=-99),
    BossEffect("얼어붙은 벽", "냉기 장막 때문에 공격 횟수가 1회 줄어듭니다.", plays_delta=-1),
    BossEffect("붉은 여왕", "♥ 카드는 데미지에 기여하지 않습니다.", debuff_suit=Suit.HEARTS),
    BossEffect("미친 경매인", "웨이브 시작 시 물자 $5를 약탈당합니다.", money_tax=5),
    BossEffect(
        "냉혹한 심판", "하이 카드와 페어 조합은 무효(0 데미지) 처리됩니다.",
        banned_hand_types=frozenset({HandType.HIGH_CARD, HandType.PAIR}),
    ),
    BossEffect("황금 사슬", "♣ 카드는 데미지에 기여하지 않습니다.", debuff_suit=Suit.CLUBS),
    BossEffect(
        "폭풍의 눈", "스트레이트와 플러시 조합은 무효(0 데미지) 처리됩니다.",
        banned_hand_types=frozenset({HandType.STRAIGHT, HandType.FLUSH}),
    ),
    BossEffect("검은 모래", "♠ 카드는 데미지에 기여하지 않습니다.", debuff_suit=Suit.SPADES),
    BossEffect("차가운 유리", "♦ 카드는 데미지에 기여하지 않습니다.", debuff_suit=Suit.DIAMONDS),
    BossEffect(
        "굳은 손가락", "한 번에 최대 2장까지만 공격에 쓸 수 있습니다.", max_cards_per_play=2,
    ),
    BossEffect(
        "졸린 오후", "한 번에 최대 3장까지만 공격에 쓸 수 있습니다.", max_cards_per_play=3,
    ),
    BossEffect(
        "그림자 재판관", "트리플과 포카드 조합은 무효(0 데미지) 처리됩니다.",
        banned_hand_types=frozenset({HandType.THREE_OF_A_KIND, HandType.FOUR_OF_A_KIND}),
    ),
    BossEffect(
        "메아리 없는 방", "유물로 얻는 배율 보너스가 절반만 적용됩니다.", joker_mult_scale=0.5,
    ),
    BossEffect(
        "속삭이는 안개", "유물로 얻는 배율 보너스가 30%만 적용됩니다.", joker_mult_scale=0.3,
    ),
    BossEffect(
        "얼굴 없는 왕국", "그림 카드(J/Q/K)는 데미지에 기여하지 않습니다.", debuff_ranks=_FACE_RANKS,
    ),
    BossEffect(
        "짝수의 저주", "짝수 카드(2/4/6/8/10/Q)는 데미지에 기여하지 않습니다.", debuff_ranks=_EVEN_RANKS,
    ),
    BossEffect(
        "홀수의 저주", "홀수 카드(3/5/7/9/J/K/A)는 데미지에 기여하지 않습니다.", debuff_ranks=_ODD_RANKS,
    ),
]


def _intensify(effect):
    """위협도 최고 단계에서 보스 몬스터를 한 단계 더 흉포하게 만든다.
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
        Blind("small", "1차 웨이브", small),
        Blind("big", "2차 웨이브", big),
        Blind("boss", f"보스 웨이브 · {boss_effect.name}", boss, boss_effect),
    ]
