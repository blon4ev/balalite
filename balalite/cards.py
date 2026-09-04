from dataclasses import dataclass
from enum import Enum
from typing import Optional
import random


class Suit(Enum):
    SPADES = ("♠", "black")
    HEARTS = ("♥", "red")
    DIAMONDS = ("♦", "red")
    CLUBS = ("♣", "black")

    def __init__(self, symbol, color):
        self.symbol = symbol
        self.color = color


class Rank(Enum):
    TWO = (2, "2", 2)
    THREE = (3, "3", 3)
    FOUR = (4, "4", 4)
    FIVE = (5, "5", 5)
    SIX = (6, "6", 6)
    SEVEN = (7, "7", 7)
    EIGHT = (8, "8", 8)
    NINE = (9, "9", 9)
    TEN = (10, "10", 10)
    JACK = (11, "J", 10)
    QUEEN = (12, "Q", 10)
    KING = (13, "K", 10)
    ACE = (14, "A", 11)

    def __init__(self, order, label, chips):
        self.order = order
        self.label = label
        self.chips = chips


ENHANCEMENT_LABELS = {
    "bonus": "보너스",
    "mult": "멀티",
    "wild": "와일드",
    "glass": "유리",
}

EDITION_LABELS = {
    "foil": "포일",
    "holographic": "홀로그래픽",
    "polychrome": "폴리크롬",
}

SEAL_LABELS = {
    "red": "적색",
    "gold": "금색",
    "blue": "청색",
}


@dataclass
class Card:
    rank: Rank
    suit: Suit
    enhancement: Optional[str] = None
    edition: Optional[str] = None
    seal: Optional[str] = None

    def __str__(self):
        return f"{self.suit.symbol} {self.rank.label}"


def card_to_dict(card):
    return {
        "rank": card.rank.name,
        "suit": card.suit.name,
        "enhancement": card.enhancement,
        "edition": card.edition,
        "seal": card.seal,
    }


def card_from_dict(data):
    return Card(
        Rank[data["rank"]],
        Suit[data["suit"]],
        enhancement=data.get("enhancement"),
        edition=data.get("edition"),
        seal=data.get("seal"),
    )


class Deck:
    """런 전체에서 유지되는 52장의 카드 풀. 카드 강화 상태가 라운드를 넘어 유지되도록
    매 라운드 새로 만들지 않고, 낸/버린 카드를 discard_pile에 모았다가 재셔플한다."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.discard_pile = []
        self.rng.shuffle(self.cards)

    def draw(self, count):
        drawn = []
        for _ in range(count):
            if not self.cards:
                self._recycle()
            if not self.cards:
                break
            drawn.append(self.cards.pop())
        return drawn

    def discard(self, cards):
        self.discard_pile.extend(cards)

    def _recycle(self):
        self.cards.extend(self.discard_pile)
        self.discard_pile = []
        self.rng.shuffle(self.cards)

    def reshuffle_round(self, leftover_hand):
        """라운드 시작 시 이전 손패를 회수하고 전체를 다시 섞는다."""
        self.discard(leftover_hand)
        self._recycle()
