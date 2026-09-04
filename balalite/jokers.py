from dataclasses import dataclass
from typing import Callable, List

from .cards import Rank, Suit
from .scoring import HandType

RARITY_WEIGHT = {
    "common": 10,
    "uncommon": 5,
    "rare": 2,
    "legendary": 1,
}
RARITY_LABEL = {
    "common": "커먼",
    "uncommon": "언커먼",
    "rare": "레어",
    "legendary": "레전더리",
}


class ScoreContext:
    def __init__(self, played_cards, scoring_cards, hand_type, chips, mult, game=None):
        self.played_cards = played_cards
        self.scoring_cards = scoring_cards
        self.hand_type = hand_type
        self.chips = chips
        self.mult = mult
        self.game = game


@dataclass(frozen=True)
class Joker:
    key: str
    name: str
    description: str
    cost: int
    timing: str  # "add" 먼저 적용, "mult_x" 나중에 적용
    effect: Callable[[ScoreContext], None]
    rarity: str = "common"


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


def _club_lover(ctx):
    ctx.mult += 2 * sum(1 for c in ctx.played_cards if c.suit is Suit.CLUBS)


def _spade_guardian(ctx):
    ctx.mult += 2 * sum(1 for c in ctx.played_cards if c.suit is Suit.SPADES)


def _even_lover(ctx):
    ctx.mult += sum(1 for c in ctx.scoring_cards if c.rank.order % 2 == 0)


def _odd_lover(ctx):
    ctx.mult += sum(1 for c in ctx.scoring_cards if c.rank.order % 2 == 1)


def _ace_killer(ctx):
    if any(c.rank is Rank.ACE for c in ctx.scoring_cards):
        ctx.chips += 15


def _king_pride(ctx):
    if any(c.rank is Rank.KING for c in ctx.scoring_cards):
        ctx.mult += 8


def _minimalist(ctx):
    if len(ctx.played_cards) == 1:
        ctx.chips += 20


def _full_house_lover(ctx):
    if ctx.hand_type is HandType.FULL_HOUSE:
        ctx.mult += 12


def _quad_fanatic(ctx):
    if ctx.hand_type is HandType.FOUR_OF_A_KIND:
        ctx.mult += 20


def _straight_hunter(ctx):
    if ctx.hand_type in (HandType.STRAIGHT, HandType.STRAIGHT_FLUSH):
        ctx.mult += 10


def _miser(ctx):
    if ctx.game:
        ctx.mult += min(5, ctx.game.money // 10)


def _pauper(ctx):
    if ctx.game and ctx.game.money < 5:
        ctx.chips += 10


def _leisurely(ctx):
    if ctx.game:
        ctx.mult += 2 * ctx.game.discards_left


def _passionate(ctx):
    if ctx.game:
        ctx.chips += 3 * ctx.game.plays_left


def _collector(ctx):
    if ctx.game:
        ctx.mult += 2 * sum(ctx.game.hand_levels.values())


def _glass_artisan(ctx):
    ctx.chips += 10 * sum(1 for c in ctx.scoring_cards if c.enhancement == "glass")


def _wild_dancer(ctx):
    ctx.mult += 6 * sum(1 for c in ctx.scoring_cards if c.enhancement == "wild")


def _golden_hand(ctx):
    if ctx.game:
        ctx.game.money += 1


def _grinder(ctx):
    if ctx.hand_type is HandType.HIGH_CARD:
        ctx.chips += 10


def _two_pair_pro(ctx):
    if ctx.hand_type is HandType.TWO_PAIR:
        ctx.mult += 10


def _triple_master(ctx):
    if ctx.hand_type is HandType.THREE_OF_A_KIND:
        ctx.mult += 12


def _almighty(ctx):
    n = len(ctx.scoring_cards)
    ctx.chips += 5 * n
    ctx.mult += 2 * n


JOKER_POOL: List[Joker] = [
    Joker("joker_basic", "조커", "+4 Mult", 4, "add", _joker_basic, "common"),
    Joker("chip_stacker", "칩 스태커", "+30 Chips", 4, "add", _chip_stacker, "common"),
    Joker("heart_lover", "하트 러버", "플레이한 ♥ 카드 1장당 +3 Mult", 5, "add", _heart_lover, "common"),
    Joker("diamond_greed", "그리디", "플레이한 ♦ 카드 1장당 +2 Mult", 5, "add", _diamond_greed, "common"),
    Joker("flush_fanatic", "플러시 매니아", "플러시 계열 족보일 때 카드 1장당 +3 Mult", 6, "add", _flush_fanatic, "uncommon"),
    Joker("pair_booster", "페어 부스터", "페어 이상 족보일 때 +8 Mult", 5, "add", _pair_booster, "common"),
    Joker("high_stakes", "하이 스테이크", "5장을 모두 플레이하면 Mult x1.5", 7, "mult_x", _high_stakes, "uncommon"),
    Joker("face_collector", "페이스 수집가", "플레이한 J/Q/K 카드 1장당 +5 Chips", 5, "add", _face_collector, "common"),
    Joker("club_lover", "클럽 마니아", "플레이한 ♣ 카드 1장당 +2 Mult", 5, "add", _club_lover, "common"),
    Joker("spade_guardian", "스페이드 수호자", "플레이한 ♠ 카드 1장당 +2 Mult", 5, "add", _spade_guardian, "common"),
    Joker("even_lover", "짝수 애호가", "점수에 포함된 짝수 카드 1장당 +1 Mult", 4, "add", _even_lover, "common"),
    Joker("odd_lover", "홀수 애호가", "점수에 포함된 홀수 카드 1장당 +1 Mult", 4, "add", _odd_lover, "common"),
    Joker("ace_killer", "에이스 킬러", "점수에 에이스가 포함되면 +15 Chips", 5, "add", _ace_killer, "common"),
    Joker("king_pride", "킹의 자존심", "점수에 King이 포함되면 +8 Mult", 5, "add", _king_pride, "common"),
    Joker("minimalist", "미니멀리스트", "카드를 1장만 플레이하면 +20 Chips", 6, "add", _minimalist, "uncommon"),
    Joker("full_house_lover", "풀하우스 애호가", "풀 하우스일 때 +12 Mult", 6, "add", _full_house_lover, "uncommon"),
    Joker("quad_fanatic", "포카드 광신도", "포카드일 때 +20 Mult", 9, "add", _quad_fanatic, "rare"),
    Joker("straight_hunter", "스트레이트 사냥꾼", "스트레이트 계열일 때 +10 Mult", 6, "add", _straight_hunter, "uncommon"),
    Joker("miser", "구두쇠", "보유 자금 $10당 +1 Mult (최대 +5)", 6, "add", _miser, "uncommon"),
    Joker("pauper", "빚쟁이", "보유 자금이 $5 미만이면 +10 Chips", 4, "add", _pauper, "common"),
    Joker("leisurely", "여유주의자", "남은 버리기 1회당 +2 Mult", 6, "add", _leisurely, "uncommon"),
    Joker("passionate", "정열가", "남은 플레이 1회당 +3 Chips", 5, "add", _passionate, "common"),
    Joker("collector", "수집가", "족보 강화 레벨 합계 1당 +2 Mult", 8, "add", _collector, "rare"),
    Joker("glass_artisan", "유리공예가", "점수에 포함된 유리 강화 카드 1장당 +10 Chips", 6, "add", _glass_artisan, "uncommon"),
    Joker("wild_dancer", "와일드 댄서", "점수에 포함된 와일드 강화 카드 1장당 +6 Mult", 6, "add", _wild_dancer, "uncommon"),
    Joker("golden_hand", "황금손", "카드를 플레이할 때마다 +$1", 8, "add", _golden_hand, "rare"),
    Joker("grinder", "노가다꾼", "하이 카드로 낼 때 +10 Chips", 4, "add", _grinder, "common"),
    Joker("two_pair_pro", "투 페어 전문가", "투 페어일 때 +10 Mult", 5, "add", _two_pair_pro, "common"),
    Joker("triple_master", "트리플 마스터", "트리플일 때 +12 Mult", 6, "add", _triple_master, "uncommon"),
    Joker("almighty", "만능 조커", "점수에 포함된 카드 1장당 +5 Chips, +2 Mult", 14, "add", _almighty, "legendary"),
]


def apply_jokers(owned_jokers, played_cards, scoring_cards, hand_type, chips, mult, game=None):
    ctx = ScoreContext(played_cards, scoring_cards, hand_type, chips, mult, game=game)
    for j in owned_jokers:
        if j.timing == "add":
            j.effect(ctx)
    for j in owned_jokers:
        if j.timing == "mult_x":
            j.effect(ctx)
    return ctx.chips, ctx.mult
