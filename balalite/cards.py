from dataclasses import dataclass
from enum import Enum
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


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self):
        return f"{self.rank.label}{self.suit.symbol}"


class Deck:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.cards = []
        self.reset()

    def reset(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.rng.shuffle(self.cards)

    def draw(self, count):
        drawn = []
        for _ in range(count):
            if not self.cards:
                self.reset()
            drawn.append(self.cards.pop())
        return drawn
