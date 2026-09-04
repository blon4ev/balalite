from dataclasses import dataclass
from typing import Optional

# 발라트로의 "덱 선택" 시스템에서 영감을 받은, 이 프로젝트만의 자체 설계 덱 목록.
# 실제 발라트로 덱의 이름·수치를 그대로 옮긴 것이 아니라, "런 시작 규칙이 달라진다"는
# 메커니즘만 차용해 트레이드오프가 있는 원본 조합으로 구성했다.


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
    starting_joker_rarity: Optional[str] = None  # 지정 시 해당 희귀도 조커 1개를 무료로 시작 보유
    pre_enhanced_card_count: int = 0  # 런 시작 시 덱에서 무작위 카드 N장에 무작위 강화 부여


DECK_POOL = [
    DeckType(
        "deck_standard", "표준 덱",
        "아무 특이사항 없는 기본 구성입니다.",
    ),
    DeckType(
        "deck_merchant", "상인의 덱",
        "시작 자금이 $7 늘어나지만, 손패 크기가 1장 줄어듭니다.",
        money_delta=7, hand_size_delta=-1,
    ),
    DeckType(
        "deck_scholar", "학자의 덱",
        "손패 크기가 1장 늘어나지만, 시작 자금이 $2 줄어듭니다.",
        hand_size_delta=1, money_delta=-2,
    ),
    DeckType(
        "deck_recruit", "신병의 덱",
        "런 시작 시 무작위 커먼 조커 1개를 무료로 보유한 채 시작합니다.",
        starting_joker_rarity="common",
    ),
    DeckType(
        "deck_gambler", "도박꾼의 덱",
        "상점 리롤 기본 비용이 $1 저렴해지지만, 시작 자금이 $2 줄어듭니다.",
        reroll_cost_delta=-1, money_delta=-2,
    ),
    DeckType(
        "deck_reckless", "무모한 덱",
        "조커 슬롯이 1개 늘어나지만, 모든 블라인드 목표 점수가 15% 높아집니다.",
        joker_slot_delta=1, blind_requirement_multiplier=1.15,
    ),
    DeckType(
        "deck_alchemist", "연금술사의 덱",
        "소모품 슬롯이 1개 늘어나지만, 시작 자금이 $2 줄어듭니다.",
        consumable_slot_delta=1, money_delta=-2,
    ),
    DeckType(
        "deck_wild", "야생의 덱",
        "런 시작 시 덱의 무작위 카드 5장에 무작위 강화가 미리 붙어 있습니다.",
        pre_enhanced_card_count=5,
    ),
]


def deck_by_key(key):
    return next((d for d in DECK_POOL if d.key == key), DECK_POOL[0])
