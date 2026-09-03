from dataclasses import dataclass

MAX_ANTE = 8

BOSS_NAMES = [
    "가위손", "그림자 손님", "얼어붙은 벽", "붉은 여왕",
    "미친 경매인", "냉혹한 심판", "황금 사슬", "폭풍의 눈",
]


@dataclass
class Blind:
    kind: str  # "small" | "big" | "boss"
    label: str
    requirement: int


def make_blinds(ante):
    base = 300 * (1.6 ** (ante - 1))
    small = int(round(base / 10) * 10)
    big = int(round(base * 1.5 / 10) * 10)
    boss = int(round(base * 2 / 10) * 10)
    boss_name = BOSS_NAMES[(ante - 1) % len(BOSS_NAMES)]
    return [
        Blind("small", "스몰 블라인드", small),
        Blind("big", "빅 블라인드", big),
        Blind("boss", f"보스 블라인드 · {boss_name}", boss),
    ]
