from dataclasses import dataclass
from typing import Optional

# 런 시작 규칙이 달라지는 "생존자 클래스" 목록. 자체 설계 트레이드오프 조합이며,
# 손패/자금/유물·보급품 슬롯/웨이브 난이도/보급소 리롤가를 서로 맞바꾼다.


@dataclass(frozen=True)
class DeckType:
    key: str
    name: str
    description: str
    money_delta: int = 0
    hand_size_delta: int = 0
    joker_slot_delta: int = 0
    consumable_slot_delta: int = 0
    blind_requirement_multiplier: float = 1.0
    reroll_cost_delta: int = 0
    starting_joker_rarity: Optional[str] = None  # 지정 시 해당 희귀도 유물 1개를 무료로 시작 보유
    pre_enhanced_card_count: int = 0  # 런 시작 시 덱에서 무작위 카드 N장에 무작위 강화 부여


DECK_POOL = [
    DeckType(
        "deck_standard", "평범한 생존자",
        "아무 특이사항 없는 기본 구성입니다.",
    ),
    DeckType(
        "deck_merchant", "행상인 생존자",
        "시작 자금이 $7 늘어나지만, 카드 패 크기가 1장 줄어듭니다.",
        money_delta=7, hand_size_delta=-1,
    ),
    DeckType(
        "deck_scholar", "정찰병 생존자",
        "카드 패 크기가 1장 늘어나지만, 시작 자금이 $2 줄어듭니다.",
        hand_size_delta=1, money_delta=-2,
    ),
    DeckType(
        "deck_recruit", "신병 생존자",
        "생존을 시작할 때 무작위 커먼 유물 1개를 무료로 보유한 채 시작합니다.",
        starting_joker_rarity="common",
    ),
    DeckType(
        "deck_gambler", "도박꾼 생존자",
        "보급소 리롤 기본 비용이 $1 저렴해지지만, 시작 자금이 $2 줄어듭니다.",
        reroll_cost_delta=-1, money_delta=-2,
    ),
    DeckType(
        "deck_reckless", "돌격병 생존자",
        "유물 슬롯이 1개 늘어나지만, 모든 웨이브 목표 데미지가 15% 높아집니다.",
        joker_slot_delta=1, blind_requirement_multiplier=1.15,
    ),
    DeckType(
        "deck_alchemist", "화학자 생존자",
        "보급품 슬롯이 1개 늘어나지만, 시작 자금이 $2 줄어듭니다.",
        consumable_slot_delta=1, money_delta=-2,
    ),
    DeckType(
        "deck_wild", "부랑자 생존자",
        "생존을 시작할 때 덱의 무작위 카드 5장에 무작위 강화가 미리 붙어 있습니다 (주워 모은 개조 장비).",
        pre_enhanced_card_count=5,
    ),
]


def deck_by_key(key):
    return next((d for d in DECK_POOL if d.key == key), DECK_POOL[0])
