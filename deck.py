"""
Deck class for Video Poker.

Represents a single or multi-deck shoe using two parallel lists as required
by the project spec:
  deck_counts[i]  - how many of card i remain (starts at num_decks per card)
  deck_images[i]  - absolute path to the image file for card i

Card index encoding (per spec):
  index // 13 -> suit  (0=Spades, 1=Diamonds, 2=Clubs, 3=Hearts)
  index % 13  -> face  (0=Ace, 1=Two, 2=Three, ..., 9=Ten, 10=Jack, 11=Queen, 12=King)
"""

import random
from pathlib import Path

ASSETS_DIR: Path = Path(__file__).parent / "assets"

CARD_BACK: str = str(ASSETS_DIR / "Yellow_back.jpg")

_SUITS = ("Spades", "Diamonds", "Clubs", "Hearts")
_FACES = (
    "Ace",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Jack",
    "Queen",
    "King",
)


def _build_image_list() -> list[str]:
    """Build the 52-element image path list in suit-major order."""
    images: list[str] = []
    for suit in _SUITS:
        for face in _FACES:
            images.append(str(ASSETS_DIR / f"{face}_of_{suit}.gif"))
    return images


class Deck:
    """A shoe of one or more standard 52-card decks.

    Attributes:
        num_decks: Number of decks in the shoe (1-10).
        cards_dealt: Cards dealt since last reshuffle.
        total_cards: Total cards in the shoe (num_decks * 52).
        should_reshuffle: True when 60% or more of the shoe has been dealt.
    """

    def __init__(self, num_decks: int = 1) -> None:
        """Initialize a fresh shoe.

        Args:
            num_decks: Number of decks to use (1-10).

        Raises:
            ValueError: If num_decks is outside 1-10.
        """
        if not (1 <= num_decks <= 10):
            raise ValueError("num_decks must be between 1 and 10")
        self.__num_decks: int = num_decks
        self.__deck_images: list[str] = _build_image_list()
        self.__deck_counts: list[int] = [num_decks] * 52
        self.__cards_dealt: int = 0

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def num_decks(self) -> int:
        """Number of decks in this shoe."""
        return self.__num_decks

    @property
    def cards_dealt(self) -> int:
        """Cards dealt since the last reshuffle."""
        return self.__cards_dealt

    @property
    def total_cards(self) -> int:
        """Total cards in the shoe."""
        return self.__num_decks * 52

    @property
    def should_reshuffle(self) -> bool:
        """True when at least 60% of the shoe has been dealt."""
        return self.__cards_dealt / self.total_cards >= 0.60

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def deal_card(self) -> int:
        """Deal one card using rejection sampling (per spec).

        Picks a random index 0-51; if that card's count is zero, retries.
        Decrements the count and increments the dealt counter on success.

        Returns:
            The card index (0-51) of the dealt card.

        Raises:
            RuntimeError: If the shoe is completely empty.
        """
        if self.__cards_dealt >= self.total_cards:
            raise RuntimeError("Shoe is empty — call reshuffle() before dealing")
        while True:
            index: int = random.randint(0, 51)
            if self.__deck_counts[index] > 0:
                self.__deck_counts[index] -= 1
                self.__cards_dealt += 1
                return index

    def reshuffle(self) -> None:
        """Reset all card counts and the dealt counter (all cards back in shoe)."""
        self.__deck_counts = [self.__num_decks] * 52
        self.__cards_dealt = 0

    def image_for(self, card_index: int) -> str:
        """Return the image file path for a card index.

        Args:
            card_index: Integer 0-51.

        Returns:
            Absolute path string to the card's .gif image.

        Raises:
            ValueError: If card_index is outside 0-51.
        """
        if not (0 <= card_index <= 51):
            raise ValueError("card_index must be between 0 and 51")
        return self.__deck_images[card_index]

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Deck(num_decks={self.__num_decks}, "
            f"dealt={self.__cards_dealt}/{self.total_cards})"
        )
