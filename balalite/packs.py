from dataclasses import dataclass


@dataclass(frozen=True)
class Pack:
    key: str
    name: str
    description: str
    cost: int
    pack_type: str  # "joker" | "consumable" | "card"
    show_count: int
    pick_count: int
    kind: str = "pack"


PACK_POOL = [
    Pack("pack_joker", "조커 팩", "무작위 조커 3개 중 1개를 무료로 선택합니다.", 6, "joker", 3, 1),
    Pack("pack_joker_jumbo", "점보 조커 팩", "무작위 조커 4개 중 2개를 무료로 선택합니다.", 10, "joker", 4, 2),
    Pack("pack_consumable", "소모품 팩", "무작위 소모품 3개 중 1개를 무료로 선택합니다.", 6, "consumable", 3, 1),
    Pack("pack_consumable_jumbo", "점보 소모품 팩", "무작위 소모품 4개 중 2개를 무료로 선택합니다.", 10, "consumable", 4, 2),
    Pack(
        "pack_standard", "카드 팩",
        "무작위 플레잉 카드 3장 중 1장을 무료로 골라 덱에 추가합니다 (강화·에디션·씰이 미리 붙어 있을 수 있음).",
        6, "card", 3, 1,
    ),
    Pack(
        "pack_standard_jumbo", "점보 카드 팩",
        "무작위 플레잉 카드 4장 중 2장을 무료로 골라 덱에 추가합니다 (강화·에디션·씰이 미리 붙어 있을 수 있음).",
        10, "card", 4, 2,
    ),
]
