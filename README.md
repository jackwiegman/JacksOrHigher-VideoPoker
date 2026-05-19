# Video Poker Game

A fully-featured video poker game with a Tkinter GUI, persistent player saves, two game variants, sound effects, and a comprehensive unit test suite.

---

## Features

- **Two game variants**: Jacks or Better and Deuces Wild
- **Animated card dealing**: Sequential flip animations with configurable delay
- **Persistent player saves**: Bank balance saved between sessions per player name
- **Multi-deck shoe**: Configurable 1–10 decks with automatic reshuffle at 60% depletion
- **Full betting system**: Bet One Coin, custom Bet Amount (spinbox dialog), and All In
- **Sound effects**: Win/loss audio via pythonGraph library
- **96 unit tests** across three test modules covering all game logic

---

## Screenshots

| Startup | Gameplay |
|---------|----------|
| Modal dialogs guide the player through name entry, bank funding, deck count, and variant selection | Casino-green table with 5 card slots, Keep/Discard controls, payout table, and bet/bank display |

---

## Project Structure

```
VideoPokerGame/
├── main.py          # Entry point — creates Tk root and launches VideoPokerApp
├── app.py           # GUI controller and game orchestration (886 lines)
├── deck.py          # Deck class — card dealing and image management
├── player.py        # Player class — bank balance with file persistence
├── scorer.py        # Hand evaluation engine for both game variants
├── test_deck.py     # Unit tests for Deck (22 tests)
├── test_player.py   # Unit tests for Player (17 tests)
├── test_scorer.py   # Unit tests for Scorer (57 tests)
├── assets/          # Card GIFs (52 cards), card back, sound files, button images
├── game_saves/      # Auto-created directory for per-player save files
└── doc/             # PlantUML architecture diagrams (class + sequence)
```

---

## Architecture

The project is split into four modules with clean separation of concerns, coordinated by the GUI controller.

### Class Overview

```
VideoPokerApp (app.py)
├── owns → Player (player.py)
├── owns → Deck (deck.py)
└── calls → evaluate() / evaluate_deuces_wild() (scorer.py)
```

### `deck.py` — Card Management

`Deck` manages a configurable multi-deck shoe using two parallel lists (per spec):

- `__deck_counts: list[int]` — remaining count for each of 52 card indices
- `__deck_images: list[str]` — absolute path to each card's GIF asset

Cards are indexed 0–51 where `index // 13` gives suit (Spades/Diamonds/Clubs/Hearts) and `index % 13` gives face (Ace through King). Dealing uses a rejection-sampling loop: pick a random index, retry if depleted, then decrement the count. Reshuffle triggers automatically when ≥ 60% of the shoe is dealt.

### `player.py` — Persistence

`Player` stores a name and bank balance, with save/load backed by a plain-text file at `game_saves/<name>.txt`. The directory is created on first save. The setter rejects negative balances; loading a corrupted file raises `ValueError` so the GUI can handle it gracefully.

### `scorer.py` — Hand Evaluation

Two pure functions evaluate a 5-card hand (list of card indices) and return a `(hand_name, payout_multiplier)` tuple:

**`evaluate(hand)`** — Jacks or Better  
Builds `suit_checker[4]` and `face_checker[13]` count arrays, then tests hands from highest to lowest: Royal Flush → Straight Flush → Four of a Kind → Full House → Flush → Straight → Three of a Kind → Two Pair → Jacks or Better → No Win.

Straight detection uses a sliding-window product over `face_checker` — if the product of any 5 consecutive entries equals 1, a straight is present. The window wraps modulo 13 to handle both Ace-high and Ace-low straights across all 10 possible windows.

**`evaluate_deuces_wild(hand)`** — Deuces Wild  
Separates Twos (wild) from non-wild cards, then tests an extended hand hierarchy: Five of a Kind → Royal Flush → Straight Flush → Four of a Kind → Full House → Flush → Straight → Three of a Kind → Two Pair → Pair of Jacks or Better → No Win. Wild-card straight detection rejects hands where non-wild cards already contain a pair (which blocks any straight) and finds the first legal 5-rank window that the wilds can fill.

### `app.py` — GUI and Game Controller

`VideoPokerApp` implements a **5-state state machine** to coordinate all UI transitions:

| State | Description |
|-------|-------------|
| `_STARTUP` | Collecting player name, funds, deck count, variant |
| `_BETTING` | Accepting bets; Deal/Draw button locked |
| `_ANIMATING` | Cards flipping; all controls locked |
| `_DEALT` | Cards revealed; Keep/Discard active |
| `_SCORING` | Drawing replacement cards; controls locked |

State transitions prevent invalid actions (e.g., betting during animation or dealing before placing a bet).

**Key implementation details:**

- `PhotoImage` objects are cached in a list to prevent garbage collection, which would blank the displayed cards
- Card GIFs are 50×70px originals zoomed 2× to 100×140px using `PhotoImage.zoom(2, 2)`
- The card back is synthesized programmatically (nested yellow/navy rectangles on a Canvas), avoiding an external asset dependency
- Startup dialogs are deferred 100ms via `root.after()` to allow the main window to fully render before the first `Toplevel` appears
- In Deuces Wild mode, Two cards are forced to Keep and styled with an orange "★WILD" button that cannot be toggled

---

## Setup

**Requirements**: Python 3.8+ with Tkinter (included in standard CPython distributions).  
Optional: `pythonGraph` library for sound effects.

```bash
# Clone or unzip the project, then navigate to the game directory
cd VideoPokerGame

# (Optional) Create and activate a virtual environment
python -m venv poker_venv
source poker_venv/bin/activate   # Windows: poker_venv\Scripts\activate

# (Optional) Install sound library for audio effects
pip install pythonGraph
```

No other third-party packages are required.

---

## Running the Game

```bash
python main.py
```

On launch, a sequence of modal dialogs will prompt for:
1. **Player name** — used to find or create a save file
2. **Starting funds** — only shown for new players (returning players load their saved bank)
3. **Number of decks** — 1 to 10 (affects shoe size and reshuffle frequency)
4. **Game variant** — Jacks or Better or Deuces Wild

### Controls

| Button | Action |
|--------|--------|
| **Bet One Coin** | Add 1 coin to current bet (up to 50 max) |
| **Bet Amount** | Open spinbox dialog to set an exact bet amount |
| **All In** | Bet the entire remaining bank (capped at 50 coins) |
| **Deal / Draw** | Deal initial hand (during betting) or draw replacement cards (after keeping/discarding) |
| **Keep / Discard** | Toggle each card's hold status before drawing |
| **Exit** | Save player bank and close the application |

Each coin is worth $5.00. The full payout table is displayed at the bottom of the window.

---

## Running the Tests

```bash
# Run all tests from the VideoPokerGame directory
python -m unittest discover -v

# Or run individual test modules
python -m unittest test_deck -v
python -m unittest test_player -v
python -m unittest test_scorer -v
```

The test suite contains **96 unit tests** covering:

- `test_deck.py` (22 tests): Deck initialization, dealing distribution, reshuffle threshold, image path lookups, and error cases for invalid inputs
- `test_player.py` (17 tests): Bank get/set validation, `add_funds`, save/load round-trips, file corruption detection, and auto-directory creation
- `test_scorer.py` (57 tests): Every hand ranking in both Jacks or Better and Deuces Wild, payout table validation, edge cases (Ace-high vs. Ace-low straights, full house with one wild, five-of-a-kind), and invalid hand rejection

---

## Payout Tables

### Jacks or Better

| Hand | Multiplier |
|------|-----------|
| Royal Flush | 2,000× |
| Straight Flush | 250× |
| Four of a Kind | 125× |
| Full House | 40× |
| Flush | 25× |
| Straight | 20× |
| Three of a Kind | 15× |
| Two Pair | 10× |
| Jacks or Better | 5× |
| No Win | 0× |

### Deuces Wild

| Hand | Multiplier |
|------|-----------|
| Five of a Kind | 5,000× |
| Royal Flush | 2,000× |
| Straight Flush | 250× |
| Four of a Kind | 125× |
| Full House | 40× |
| Flush | 25× |
| Straight | 20× |
| Three of a Kind | 15× |
| Two Pair | 10× |
| Pair of Jacks or Better | 5× |
| No Win | 0× |

---

## Technical Highlights

- **Rejection-sampling card deal**: Statistically unbiased dealing without ever mutating or shuffling a list — just decrement counts and retry on collision
- **Circular straight detection**: A sliding window of size 5 over `face_checker` with modulo 13 wrapping covers all valid straights including Ace-low and Ace-high in a single loop
- **Wild-card straight logic**: `_is_straight_wild()` detects whether a given number of wilds can fill any 5-rank window around the non-wild faces, correctly rejecting cases where non-wild cards form a pair
- **State machine UI**: Five named states and explicit transition functions make the control flow auditable and prevent the need for scattered flag checks throughout the event handlers
- **Modal-first startup**: Sequential Toplevel dialogs eliminate async complexity — each question blocks until answered, giving a linear initialization path

---

## Author

Jack Wiegman
