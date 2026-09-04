from dataclasses import dataclass

# 난이도(위협도) 단계. 숫자가 높을수록 아래 효과가 전부 누적 적용된다
# (단계별로 이전 단계 효과 위에 하나씩 더해짐).


@dataclass(frozen=True)
class Stake:
    level: int
    key: str
    name: str
    description: str


STAKE_POOL = [
    Stake(1, "stake_1", "1단계 · 평온", "추가 효과가 없는 기본 난이도입니다."),
    Stake(2, "stake_2", "2단계 · 긴축", "1차 웨이브를 클리어해도 보상을 받지 못합니다. (이전 단계 효과 누적)"),
    Stake(3, "stake_3", "3단계 · 압박", "모든 웨이브 목표 데미지가 10% 늘어납니다. (이전 단계 효과 누적)"),
    Stake(4, "stake_4", "4단계 · 인색", "웨이브당 재정비 횟수가 1회 줄어듭니다. (이전 단계 효과 누적)"),
    Stake(5, "stake_5", "5단계 · 최후의 밤", "유물 슬롯이 1개 줄어들고, 보스 웨이브가 더 흉포해집니다. (이전 단계 효과 누적)"),
]


def stake_by_level(level):
    for s in STAKE_POOL:
        if s.level == level:
            return s
    return STAKE_POOL[0]
