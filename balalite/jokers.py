from dataclasses import dataclass
from typing import Callable, List

from .cards import Rank, Suit
from .scoring import HandType


class ScoreContext:
    def __init__(self, played_cards, scoring_cards, hand_type, chips, mult):
        self.played_cards = played_cards
        self.scoring_cards = scoring_cards
        self.hand_type = hand_type
        self.chips = chips
        self.mult = mult


@dataclass(frozen=True)
class Joker:
    key: str
    name: str
    description: str
    cost: int
    timing: str  # "add" 먼저 적용, "mult_x" 나중에 적용
    effect: Callable[[ScoreContext], None]


def _joker_basic(ctx):
    ctx.mult += 4


def _chip_stacker(ctx):
    ctx.chips += 30


def _heart_lover(ctx):
    ctx.mult += 3 * sum(1 for c in ctx.played_cards if c.suit is Suit.HEARTS)


def _diamond_greed(ctx):
    ctx.mult += 2 * sum(1 for c in ctx.played_cards if c.suit is Suit.DIAMONDS)


def _flush_fanatic(ctx):
    if ctx.hand_type in (HandType.FLUSH, HandType.STRAIGHT_FLUSH):
        ctx.mult += 3 * len(ctx.played_cards)


def _pair_booster(ctx):
    if ctx.hand_type is not HandType.HIGH_CARD:
        ctx.mult += 8


def _high_stakes(ctx):
    if len(ctx.played_cards) == 5:
        ctx.mult *= 1.5


def _face_collector(ctx):
    faces = sum(1 for c in ctx.played_cards if c.rank in (Rank.JACK, Rank.QUEEN, Rank.KING))
    ctx.chips += 5 * faces


JOKER_POOL: List[Joker] = [
    Joker("joker_basic", "조커", "+4 Mult", 4, "add", _joker_basic),
    Joker("chip_stacker", "칩 스태커", "+30 Chips", 4, "add", _chip_stacker),
    Joker("heart_lover", "하트 러버", "플레이한 ♥ 카드 1장당 +3 Mult", 5, "add", _heart_lover),
    Joker("diamond_greed", "그리디", "플레이한 ♦ 카드 1장당 +2 Mult", 5, "add", _diamond_greed),
    Joker("flush_fanatic", "플러시 매니아", "플러시 계열 족보일 때 카드 1장당 +3 Mult", 6, "add", _flush_fanatic),
    Joker("pair_booster", "페어 부스터", "페어 이상 족보일 때 +8 Mult", 5, "add", _pair_booster),
    Joker("high_stakes", "하이 스테이크", "5장을 모두 플레이하면 Mult x1.5", 7, "mult_x", _high_stakes),
    Joker("face_collector", "페이스 수집가", "플레이한 J/Q/K 카드 1장당 +5 Chips", 5, "add", _face_collector),
]


def apply_jokers(owned_jokers, played_cards, scoring_cards, hand_type, chips, mult):
    ctx = ScoreContext(played_cards, scoring_cards, hand_type, chips, mult)
    for j in owned_jokers:
        if j.timing == "add":
            j.effect(ctx)
    for j in owned_jokers:
        if j.timing == "mult_x":
            j.effect(ctx)
    return ctx.chips, ctx.mult
