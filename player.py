"""
Player class for Video Poker.

Manages the player's name and bank balance, with persistence to
game_saves/<name>.txt (relative to this file's directory).
"""

from pathlib import Path

SAVES_DIR: Path = Path(__file__).parent / "game_saves"


class Player:
    """A video poker player with a persistent bank balance.

    Bank is stored in coins (each worth $5.00). The save file contains
    only the raw float value of the bank balance.

    Attributes:
        name: The player's name (used as the save file stem).
        bank: Current coin balance (non-negative float).
    """

    def __init__(self, name: str) -> None:
        """Initialize a Player with zero balance.

        Call load() after construction to restore a saved balance.

        Args:
            name: The player's name.
        """
        self.__name: str = name
        self.__bank: float = 0.0

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The player's name."""
        return self.__name

    @property
    def bank(self) -> float:
        """Current coin balance."""
        return self.__bank

    @bank.setter
    def bank(self, value: float) -> None:
        """Set the bank balance.

        Args:
            value: New balance (must be >= 0).

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            raise ValueError("Bank balance cannot be negative")
        self.__bank = float(value)

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def load(self) -> bool:
        """Load the saved bank balance from game_saves/<name>.txt.

        Returns:
            True if a save file existed and was loaded, False if new player.

        Raises:
            ValueError: If the save file exists but contains invalid data.
        """
        save_file = SAVES_DIR / f"{self.__name}.txt"
        if not save_file.exists():
            return False
        try:
            self.__bank = float(save_file.read_text().strip())
        except ValueError as exc:
            raise ValueError(f"Save file for '{self.__name}' is corrupted") from exc
        return True

    def save(self) -> None:
        """Write the current bank balance to game_saves/<name>.txt.

        Creates game_saves/ if it does not exist.
        """
        SAVES_DIR.mkdir(exist_ok=True)
        save_file = SAVES_DIR / f"{self.__name}.txt"
        save_file.write_text(str(self.__bank))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def add_funds(self, coins: int) -> None:
        """Add coins to the bank.

        Args:
            coins: Number of coins to add (must be positive).

        Raises:
            ValueError: If coins is not a positive integer.
        """
        if coins <= 0:
            raise ValueError("Must add a positive number of coins")
        self.__bank += coins

    # -------------------------------------------------------------------------
    # Representation
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Player(name={self.__name!r}, bank={self.__bank:.2f})"
