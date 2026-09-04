from dataclasses import dataclass
from typing import Callable, List, Optional

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
    edition: Optional[str] = None  # "negative"면 조커 슬롯을 차지하지 않음


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


# ---------------------------------------------------------------------------
# 확장 조커 (30종 -> 100종). 아래는 전부 이 프로젝트의 자체 설계이며, 발라트로의
# 실제 조커 이름/효과/수치를 그대로 옮긴 것이 아니다. 반복되는 패턴(무늬별,
# 족보 레벨별 등)은 팩토리 함수로 생성해 코드 중복을 줄였다.
# ---------------------------------------------------------------------------

SUIT_KOREAN = {
    Suit.SPADES: "스페이드",
    Suit.HEARTS: "하트",
    Suit.DIAMONDS: "다이아몬드",
    Suit.CLUBS: "클럽",
}


def _suit_chip_bonus(suit, amount):
    def effect(ctx):
        ctx.chips += amount * sum(1 for c in ctx.played_cards if c.suit is suit)
    return effect


def _no_suit_mult_bonus(suit, amount):
    def effect(ctx):
        if not any(c.suit is suit for c in ctx.played_cards):
            ctx.mult += amount
    return effect


def _rank_present_bonus(rank, amount, target):
    def effect(ctx):
        if any(c.rank is rank for c in ctx.scoring_cards):
            if target == "chips":
                ctx.chips += amount
            else:
                ctx.mult += amount
    return effect


def _hand_scholar_effect(hand_type, per_level):
    def effect(ctx):
        if ctx.hand_type is hand_type and ctx.game:
            ctx.mult += per_level * ctx.game.hand_levels.get(hand_type, 0)
    return effect


def _enhancement_count_bonus(key, amount, target):
    def effect(ctx):
        count = sum(1 for c in ctx.scoring_cards if c.enhancement == key)
        if target == "chips":
            ctx.chips += amount * count
        else:
            ctx.mult += amount * count
    return effect


def _edition_count_chip_bonus(key, amount):
    def effect(ctx):
        count = sum(1 for c in ctx.scoring_cards if c.edition == key)
        ctx.chips += amount * count
    return effect


def _edition_count_mult_bonus(key, amount):
    def effect(ctx):
        count = sum(1 for c in ctx.scoring_cards if c.edition == key)
        ctx.mult += amount * count
    return effect


def _poly_collector_effect(ctx):
    count = sum(1 for c in ctx.scoring_cards if c.edition == "polychrome")
    if count:
        ctx.mult *= min(2.0, 1 + 0.15 * count)


SUIT_CHIP_JOKERS: List[Joker] = [
    Joker(
        f"suit_chip_{suit.name.lower()}", f"{SUIT_KOREAN[suit]}의 축복",
        f"플레이한 {suit.symbol} 카드 1장당 +8 Chips", 5, "add", _suit_chip_bonus(suit, 8), "common",
    )
    for suit in Suit
]

NO_SUIT_JOKERS: List[Joker] = [
    Joker(
        f"no_suit_{suit.name.lower()}", f"{SUIT_KOREAN[suit]} 기피자",
        f"이번 플레이에 {suit.symbol} 카드가 없으면 +6 Mult", 5, "add", _no_suit_mult_bonus(suit, 6), "common",
    )
    for suit in Suit
]

RANK_PRESENT_JOKERS: List[Joker] = [
    Joker("queen_grace", "여왕의 은총", "점수에 Q가 포함되면 +10 Chips", 5, "add",
          _rank_present_bonus(Rank.QUEEN, 10, "chips"), "common"),
    Joker("jack_wit", "잭의 재치", "점수에 J가 포함되면 +6 Mult", 5, "add",
          _rank_present_bonus(Rank.JACK, 6, "mult"), "common"),
    Joker("ten_treasure", "텐의 보물", "점수에 10이 포함되면 +12 Chips", 5, "add",
          _rank_present_bonus(Rank.TEN, 12, "chips"), "common"),
]

# 학자 조커는 룬이 처음 추가됐던 8개 표준 족보만 대상으로 한다 (히든 족보용 룬을
# 나중에 추가해도 조커 100종 구성이 흔들리지 않도록 고정 목록을 쓴다).
_SCHOLAR_HAND_TYPES = [
    HandType.PAIR, HandType.TWO_PAIR, HandType.THREE_OF_A_KIND, HandType.STRAIGHT,
    HandType.FLUSH, HandType.FULL_HOUSE, HandType.FOUR_OF_A_KIND, HandType.STRAIGHT_FLUSH,
]

HAND_TYPE_SCHOLAR_JOKERS: List[Joker] = [
    Joker(
        f"scholar_{ht.name.lower()}", f"{ht.label} 학자",
        f"{ht.label}로 낼 때, 그 족보의 룬 레벨 1당 +2 Mult",
        6 + ht.base_mult, "add", _hand_scholar_effect(ht, 2),
        "rare" if (6 + ht.base_mult) > 10 else "uncommon",
    )
    for ht in _SCHOLAR_HAND_TYPES
]

ENHANCEMENT_COUNT_JOKERS: List[Joker] = [
    Joker("bonus_appraiser", "보너스 감정사", "점수에 포함된 보너스 강화 카드 1장당 +6 Mult", 6, "add",
          _enhancement_count_bonus("bonus", 6, "mult"), "uncommon"),
    Joker("mult_appraiser", "멀티 감정사", "점수에 포함된 멀티 강화 카드 1장당 +15 Chips", 6, "add",
          _enhancement_count_bonus("mult", 15, "chips"), "uncommon"),
]

EDITION_COUNT_JOKERS: List[Joker] = [
    Joker("foil_collector", "포일 수집가", "점수에 포함된 포일 카드 1장당 +20 Chips", 8, "add",
          _edition_count_chip_bonus("foil", 20), "rare"),
    Joker("holo_collector", "홀로 수집가", "점수에 포함된 홀로그래픽 카드 1장당 +8 Mult", 8, "add",
          _edition_count_mult_bonus("holographic", 8), "rare"),
    Joker("poly_collector", "폴리 수집가", "점수에 포함된 폴리크롬 카드 1장당 Mult x1.15 (최대 x2)", 9, "mult_x",
          _poly_collector_effect, "rare"),
]


def _joker_horde(ctx):
    if ctx.game:
        ctx.mult += len(ctx.game.jokers)


def _consumable_hoarder(ctx):
    if ctx.game:
        ctx.chips += 8 * len(ctx.game.consumables)


def _voucher_scholar(ctx):
    if ctx.game:
        ctx.mult += 2 * len(ctx.game.owned_vouchers)


def _ante_veteran(ctx):
    if ctx.game:
        ctx.chips += 2 * ctx.game.ante


def _blind_slayer_boss(ctx):
    if ctx.game and ctx.game.current_blind.kind == "boss":
        ctx.mult += 15


def _blind_slayer_small(ctx):
    if ctx.game and ctx.game.current_blind.kind == "small":
        ctx.chips += 10


def _first_play_bonus(ctx):
    if ctx.game and ctx.game.plays_left == ctx.game.base_plays:
        ctx.mult += 8


def _last_stand(ctx):
    if ctx.game and ctx.game.plays_left == 1:
        ctx.mult *= 2


def _clean_hands(ctx):
    if ctx.game and ctx.game.discards_left == ctx.game.base_discards:
        ctx.chips += 20


def _discard_exhausted(ctx):
    if ctx.game and ctx.game.discards_left == 0:
        ctx.mult += 10


def _plays_low(ctx):
    if ctx.game and ctx.game.plays_left <= 1:
        ctx.chips += 12


def _frugal(ctx):
    if ctx.game and ctx.game.money <= 3:
        ctx.mult *= 1.3


def _big_spender(ctx):
    if ctx.game and ctx.game.money >= 50:
        ctx.mult += 15


def _retrigger_chips(ctx):
    ctx.chips += sum(c.rank.chips for c in ctx.scoring_cards)


def _retrigger_mult_small(ctx):
    ctx.mult += ctx.hand_type.base_mult


def _solo_act(ctx):
    if len(ctx.played_cards) == 1:
        ctx.mult *= 1.5


def _full_hand(ctx):
    if len(ctx.played_cards) == 5:
        ctx.chips += 40


def _duo_bonus(ctx):
    if len(ctx.played_cards) == 2:
        ctx.mult += 6


def _trio_bonus(ctx):
    if len(ctx.played_cards) == 3:
        ctx.chips += 20


def _quartet_bonus(ctx):
    if len(ctx.played_cards) == 4:
        ctx.mult += 9


def _omega_joker(ctx):
    ctx.chips *= 2
    ctx.mult *= 2


def _karma(ctx):
    if ctx.game:
        ctx.mult *= min(1.5, 1 + 0.1 * (ctx.game.money // 100))


def _singularity(ctx):
    n = len(ctx.scoring_cards)
    ctx.chips += n * n


def _eternal_flame(ctx):
    if ctx.game:
        total = sum(ctx.game.hand_levels.values())
        ctx.mult *= min(2.0, 1 + 0.05 * total)


def _lucky_seven(ctx):
    if any(c.rank is Rank.SEVEN for c in ctx.scoring_cards):
        ctx.chips += 21


def _even_money(ctx):
    if ctx.game and ctx.game.money % 2 == 0:
        ctx.mult += 6


def _odd_money(ctx):
    if ctx.game and ctx.game.money % 2 == 1:
        ctx.chips += 10


def _suit_majority(ctx):
    counts = {}
    for c in ctx.played_cards:
        counts[c.suit] = counts.get(c.suit, 0) + 1
    if counts and max(counts.values()) >= 3:
        ctx.mult += 10


def _straight_flush_master(ctx):
    if ctx.hand_type is HandType.STRAIGHT_FLUSH:
        ctx.mult += 40


def _rare_collector(ctx):
    if ctx.game:
        count = sum(1 for j in ctx.game.jokers if j.rarity in ("rare", "legendary"))
        ctx.mult += 5 * count


def _even_purist(ctx):
    if ctx.scoring_cards and all(c.rank.order % 2 == 0 for c in ctx.scoring_cards):
        ctx.mult += 16


def _odd_purist(ctx):
    if ctx.scoring_cards and all(c.rank.order % 2 == 1 for c in ctx.scoring_cards):
        ctx.chips += 50


def _crimson_hand(ctx):
    if ctx.played_cards and all(c.suit in (Suit.HEARTS, Suit.DIAMONDS) for c in ctx.played_cards):
        ctx.mult += 12


def _onyx_hand(ctx):
    if ctx.played_cards and all(c.suit in (Suit.SPADES, Suit.CLUBS) for c in ctx.played_cards):
        ctx.mult += 12


def _purist(ctx):
    if ctx.scoring_cards and all(c.enhancement is None for c in ctx.scoring_cards):
        ctx.mult += 8


def _edition_lover(ctx):
    if any(c.edition for c in ctx.scoring_cards):
        ctx.mult *= 1.4


def _seal_hunter(ctx):
    if any(c.seal for c in ctx.scoring_cards):
        ctx.chips += 25


def _bicolor(ctx):
    suits = {c.suit for c in ctx.played_cards}
    if len(suits) == 2:
        ctx.mult += 8


def _lowest_two(ctx):
    if ctx.played_cards and min(ctx.played_cards, key=lambda c: c.rank.order).rank is Rank.TWO:
        ctx.chips += 14


def _even_count(ctx):
    if len(ctx.played_cards) % 2 == 0:
        ctx.chips += 10


def _odd_count(ctx):
    if len(ctx.played_cards) % 2 == 1:
        ctx.mult += 6


def _full_slots_bonus(ctx):
    from .game import MAX_JOKER_SLOTS

    if ctx.game and ctx.game.joker_slot_count() >= MAX_JOKER_SLOTS:
        ctx.mult *= 1.5


def _glass_cannon(ctx):
    if any(c.enhancement == "glass" for c in ctx.scoring_cards):
        ctx.mult *= 1.8


def _wild_heart(ctx):
    if ctx.hand_type in (HandType.FLUSH, HandType.STRAIGHT_FLUSH) and any(
        c.enhancement == "wild" for c in ctx.scoring_cards
    ):
        ctx.mult += 20


def _no_face(ctx):
    if ctx.scoring_cards and not any(
        c.rank in (Rank.JACK, Rank.QUEEN, Rank.KING) for c in ctx.scoring_cards
    ):
        ctx.mult += 10


def _all_face(ctx):
    if ctx.scoring_cards and all(
        c.rank in (Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE) for c in ctx.scoring_cards
    ):
        ctx.chips += 18


BESPOKE_JOKERS: List[Joker] = [
    Joker("joker_horde", "군중 심리", "보유한 조커 1개당(본인 포함) +1 Mult", 5, "add", _joker_horde, "common"),
    Joker("consumable_hoarder", "수집벽", "보유한 소모품 1개당 +8 Chips", 5, "add", _consumable_hoarder, "common"),
    Joker("voucher_scholar", "제도학자", "보유한 바우처 1개당 +2 Mult", 7, "add", _voucher_scholar, "uncommon"),
    Joker("ante_veteran", "고참병", "현재 앤티 1당 +2 Chips", 5, "add", _ante_veteran, "common"),
    Joker("blind_slayer_boss", "보스 사냥꾼", "보스 블라인드일 때 +15 Mult", 8, "add", _blind_slayer_boss, "rare"),
    Joker("blind_slayer_small", "몸풀기", "스몰 블라인드일 때 +10 Chips", 4, "add", _blind_slayer_small, "common"),
    Joker("first_play_bonus", "선공", "이번 라운드 첫 플레이면 +8 Mult", 6, "add", _first_play_bonus, "uncommon"),
    Joker("last_stand", "막판 스퍼트", "이번 플레이가 이번 라운드 마지막 플레이면 Mult x2", 9, "mult_x", _last_stand, "rare"),
    Joker("clean_hands", "깔끔한 손", "이번 라운드에 버리기를 한 번도 안 썼으면 +20 Chips", 6, "add", _clean_hands, "uncommon"),
    Joker("discard_exhausted", "막 버리기", "버리기를 모두 소진했으면 +10 Mult", 6, "add", _discard_exhausted, "uncommon"),
    Joker("plays_low", "벼랑 끝", "남은 플레이가 1회 이하면 +12 Chips", 5, "add", _plays_low, "common"),
    Joker("frugal", "검소함", "보유 자금이 $3 이하면 Mult x1.3", 7, "mult_x", _frugal, "uncommon"),
    Joker("big_spender", "큰손", "보유 자금이 $50 이상이면 +15 Mult", 9, "add", _big_spender, "rare"),
    Joker("retrigger_chips", "메아리 손", "점수 카드들의 칩 값을 한 번 더 더함", 9, "add", _retrigger_chips, "rare"),
    Joker("retrigger_mult_small", "겹울림", "족보의 기본 배수를 한 번 더 더함", 7, "add", _retrigger_mult_small, "uncommon"),
    Joker("solo_act", "독주자", "카드를 1장만 내면 Mult x1.5", 7, "mult_x", _solo_act, "uncommon"),
    Joker("full_hand", "풀핸드", "카드를 5장 다 내면 +40 Chips", 6, "add", _full_hand, "uncommon"),
    Joker("duo_bonus", "듀오", "카드를 정확히 2장 내면 +6 Mult", 5, "add", _duo_bonus, "common"),
    Joker("trio_bonus", "트리오", "카드를 정확히 3장 내면 +20 Chips", 5, "add", _trio_bonus, "common"),
    Joker("quartet_bonus", "콰르텟", "카드를 정확히 4장 내면 +9 Mult", 6, "add", _quartet_bonus, "uncommon"),
    Joker("omega_joker", "오메가", "이 손패의 칩과 배수를 전부 2배로 만듦", 16, "mult_x", _omega_joker, "legendary"),
    Joker("karma", "인과응보", "보유 자금 $100당 Mult x1.1 (최대 x1.5)", 12, "mult_x", _karma, "legendary"),
    Joker("singularity", "특이점", "점수 카드 수의 제곱만큼 +Chips", 10, "add", _singularity, "rare"),
    Joker("eternal_flame", "영원한 불꽃", "모든 족보 룬 레벨 합계 1당 Mult x1.05 (최대 x2)", 14, "mult_x", _eternal_flame, "legendary"),
    Joker("lucky_seven", "럭키 세븐", "점수에 7이 포함되면 +21 Chips", 5, "add", _lucky_seven, "common"),
    Joker("even_money", "짝수의 밤", "보유 자금이 짝수면 +6 Mult", 4, "add", _even_money, "common"),
    Joker("odd_money", "홀수의 밤", "보유 자금이 홀수면 +10 Chips", 4, "add", _odd_money, "common"),
    Joker("suit_majority", "무늬 지배", "플레이한 카드 중 한 무늬가 3장 이상이면 +10 Mult", 6, "add", _suit_majority, "uncommon"),
    Joker("straight_flush_master", "궁극의 조합", "스트레이트 플러시면 +40 Mult", 11, "add", _straight_flush_master, "rare"),
    Joker("rare_collector", "감정가", "보유한 레어 이상 조커 1개당 +5 Mult", 10, "add", _rare_collector, "rare"),
    Joker("even_purist", "완벽한 짝수", "점수 카드가 전부 짝수면 +16 Mult", 7, "add", _even_purist, "uncommon"),
    Joker("odd_purist", "완벽한 홀수", "점수 카드가 전부 홀수면 +50 Chips", 7, "add", _odd_purist, "uncommon"),
    Joker("crimson_hand", "다홍빛 손", "플레이한 카드가 전부 빨강 무늬(♥♦)면 +12 Mult", 6, "add", _crimson_hand, "uncommon"),
    Joker("onyx_hand", "흑요석 손", "플레이한 카드가 전부 검정 무늬(♠♣)면 +12 Mult", 6, "add", _onyx_hand, "uncommon"),
    Joker("purist", "순수주의자", "점수 카드에 강화가 하나도 없으면 +8 Mult", 5, "add", _purist, "common"),
    Joker("edition_lover", "수집가의 눈", "점수 카드 중 에디션이 있으면 Mult x1.4", 10, "mult_x", _edition_lover, "rare"),
    Joker("seal_hunter", "인장 사냥꾼", "점수 카드 중 씰이 있으면 +25 Chips", 7, "add", _seal_hunter, "uncommon"),
    Joker("bicolor", "이색 조합", "플레이한 무늬가 정확히 2종류면 +8 Mult", 6, "add", _bicolor, "uncommon"),
    Joker("lowest_two", "최소주의", "낸 카드 중 가장 낮은 카드가 2면 +14 Chips", 4, "add", _lowest_two, "common"),
    Joker("even_count", "짝수 손", "낸 카드 장수가 짝수면 +10 Chips", 4, "add", _even_count, "common"),
    Joker("odd_count", "홀수 손", "낸 카드 장수가 홀수면 +6 Mult", 4, "add", _odd_count, "common"),
    Joker("full_slots_bonus", "만원사례", "조커 슬롯이 가득 찼으면 Mult x1.5", 13, "mult_x", _full_slots_bonus, "legendary"),
    Joker("glass_cannon", "유리대포", "점수 카드 중 유리 강화가 있으면 Mult x1.8", 10, "mult_x", _glass_cannon, "rare"),
    Joker("wild_heart", "와일드 하트", "플러시 계열이고 점수 카드 중 와일드 강화가 있으면 +20 Mult", 8, "add", _wild_heart, "uncommon"),
    Joker("no_face", "그림 없는 손", "점수 카드에 그림카드(J/Q/K)가 없으면 +10 Mult", 5, "add", _no_face, "common"),
    Joker("all_face", "궁정 회의", "점수 카드가 전부 J/Q/K/A면 +18 Chips", 6, "add", _all_face, "uncommon"),
]


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
] + SUIT_CHIP_JOKERS + NO_SUIT_JOKERS + RANK_PRESENT_JOKERS + HAND_TYPE_SCHOLAR_JOKERS + \
    ENHANCEMENT_COUNT_JOKERS + EDITION_COUNT_JOKERS + BESPOKE_JOKERS


def apply_jokers(owned_jokers, played_cards, scoring_cards, hand_type, chips, mult, game=None):
    ctx = ScoreContext(played_cards, scoring_cards, hand_type, chips, mult, game=game)
    for j in owned_jokers:
        if j.timing == "add":
            j.effect(ctx)
    for j in owned_jokers:
        if j.timing == "mult_x":
            j.effect(ctx)
    return ctx.chips, ctx.mult
