from dataclasses import dataclass
from typing import Callable

from .jokers import JOKER_POOL
from .vouchers import VOUCHER_POOL


@dataclass(frozen=True)
class Tag:
    key: str
    name: str
    description: str
    effect: Callable[["GameState"], None]


def _money_tag(game):
    game.money += 10
    game.last_tag_message = "황금 포상: +$10을 획득했습니다."


def _joker_tag(game):
    candidates = [j for j in JOKER_POOL if j not in game.jokers]
    if candidates and game.joker_slot_count() < game.max_joker_slots:
        joker = game.rng.choice(candidates)
        game.jokers.append(joker)
        game.last_tag_message = f"유물 포상: '{joker.name}'을(를) 무료로 획득했습니다."
    else:
        game.money += 5
        game.last_tag_message = "유물 포상: 슬롯이 없어 대신 +$5를 획득했습니다."


def _voucher_tag(game):
    candidates = [v for v in VOUCHER_POOL if v.key not in game.owned_vouchers]
    if candidates:
        voucher = game.rng.choice(candidates)
        voucher.effect(game)
        game.owned_vouchers.add(voucher.key)
        game.last_tag_message = f"훈련 포상: '{voucher.name}'을(를) 무료로 획득했습니다."
    else:
        game.money += 5
        game.last_tag_message = "훈련 포상: 획득 가능한 훈련 프로그램이 없어 대신 +$5를 획득했습니다."


TAG_POOL = [
    Tag("money_tag", "황금 포상", "즉시 $10을 얻습니다.", _money_tag),
    Tag("joker_tag", "유물 포상", "무료 유물 1개를 얻습니다 (슬롯이 없으면 $5).", _joker_tag),
    Tag("voucher_tag", "훈련 포상", "미보유 훈련 프로그램 1개를 무료로 얻습니다 (없으면 $5).", _voucher_tag),
]
