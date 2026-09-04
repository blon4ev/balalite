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
    game.last_tag_message = "황금 태그: +$10을 획득했습니다."


def _joker_tag(game):
    from .game import MAX_JOKER_SLOTS

    candidates = [j for j in JOKER_POOL if j not in game.jokers]
    if candidates and game.joker_slot_count() < MAX_JOKER_SLOTS:
        joker = game.rng.choice(candidates)
        game.jokers.append(joker)
        game.last_tag_message = f"조커 태그: '{joker.name}'을(를) 무료로 획득했습니다."
    else:
        game.money += 5
        game.last_tag_message = "조커 태그: 슬롯이 없어 대신 +$5를 획득했습니다."


def _voucher_tag(game):
    candidates = [v for v in VOUCHER_POOL if v.key not in game.owned_vouchers]
    if candidates:
        voucher = game.rng.choice(candidates)
        voucher.effect(game)
        game.owned_vouchers.add(voucher.key)
        game.last_tag_message = f"바우처 태그: '{voucher.name}'을(를) 무료로 획득했습니다."
    else:
        game.money += 5
        game.last_tag_message = "바우처 태그: 획득 가능한 바우처가 없어 대신 +$5를 획득했습니다."


TAG_POOL = [
    Tag("money_tag", "황금 태그", "즉시 $10을 얻습니다.", _money_tag),
    Tag("joker_tag", "조커 태그", "무료 조커 1개를 얻습니다 (슬롯이 없으면 $5).", _joker_tag),
    Tag("voucher_tag", "바우처 태그", "미보유 바우처 1개를 무료로 얻습니다 (없으면 $5).", _voucher_tag),
]
