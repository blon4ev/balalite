from dataclasses import dataclass

# 발라트로의 "스테이크" 난이도 시스템에서 영감을 받은 자체 설계 난이도 단계.
# 숫자가 높을수록 아래 효과가 전부 누적 적용된다 (원작처럼 단계별로 하나씩 더해짐).


@dataclass(frozen=True)
class Stake:
    level: int
    key: str
    name: str
    description: str


STAKE_POOL = [
    Stake(1, "stake_1", "1단계 · 기본", "추가 효과가 없는 기본 난이도입니다."),
    Stake(2, "stake_2", "2단계 · 긴축", "스몰 블라인드를 클리어해도 보상을 받지 못합니다. (이전 단계 효과 누적)"),
    Stake(3, "stake_3", "3단계 · 압박", "모든 블라인드 목표 점수가 10% 늘어납니다. (이전 단계 효과 누적)"),
    Stake(4, "stake_4", "4단계 · 인색", "라운드당 버리기 횟수가 1회 줄어듭니다. (이전 단계 효과 누적)"),
    Stake(5, "stake_5", "5단계 · 극한", "조커 슬롯이 1개 줄어들고, 보스 블라인드 효과가 더 강력해집니다. (이전 단계 효과 누적)"),
]


def stake_by_level(level):
    for s in STAKE_POOL:
        if s.level == level:
            return s
    return STAKE_POOL[0]
