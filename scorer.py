"""
Scorer module for Video Poker.

Implements the hand-scoring algorithm from the project spec using two checker
lists built from the five card indices in the player's hand:

  suit_checker[4]  - count of cards per suit
  face_checker[13] - count of cards per face value

A Straight is detected by checking whether the product of any five consecutive
elements (circularly) in face_checker equals 1.
"""

# Payout multipliers keyed by hand name.  Actual payout = multiplier * bet.
PAYOUTS = {
    "Royal Flush": 2000,
    "Straight Flush": 250,
    "Four of a Kind": 125,
    "Full House": 40,
    "Flush": 25,
    "Straight": 20,
    "Three of a Kind": 15,
    "Two Pair": 10,
    "Pair of Jacks or Better": 5,
    "No Win": 0,
}

# Deuces Wild payout table -Twos are wild; Five of a Kind added as top hand.
PAYOUTS_DW = {
    "Five of a Kind": 5000,
    "Royal Flush": 2000,
    "Straight Flush": 250,
    "Four of a Kind": 125,
    "Full House": 40,
    "Flush": 25,
    "Straight": 20,
    "Three of a Kind": 15,
    "Two Pair": 10,
    "Pair of Jacks or Better": 5,
    "No Win": 0,
}

# Indices in face_checker that qualify as "Jacks or Better" (Ace, Jack, Queen, King)
_JACKS_OR_BETTER = (0, 10, 11, 12)

# Royal Flush face indices: Ten, Jack, Queen, King, Ace
_ROYAL_FACES = {9, 10, 11, 12, 0}


def _is_flush(suit_checker: list[int]) -> bool:
    """Return True if all five cards share a suit."""
    return 5 in suit_checker


def _is_straight(face_checker: list[int]) -> bool:
    """Return True if any five consecutive face-checker slots (circular) are all 1.

    Per the spec: the product of five consecutive 'boxes', computed in a
    circular fashion, equals 1 when a straight is present. Only checks the
    10 valid starting positions (Ace-low through Ace-high).

    Args:
        face_checker: 13-element list of face value counts.

    Returns:
        True if a valid straight is present, False otherwise.
    """
    for i in range(10):
        product = 1
        for offset in range(5):
            product *= face_checker[(i + offset) % 13]
        if product == 1:
            return True
    return False


def _is_straight_wild(nw_faces: list[int], wilds: int) -> bool:
    """Return True if non-wild card faces + wilds can form any valid 5-card straight.

    Checks all 10 legal straight windows. Duplicate non-wild faces (a pair)
    can never contribute to a straight, so those hands return False immediately.

    Args:
        nw_faces: Face indices of non-wild cards.
        wilds: Number of wild cards in hand.

    Returns:
        True if a straight is achievable, False otherwise.
    """
    if wilds >= 4:
        return True
    unique = sorted(set(nw_faces))
    if len(unique) < len(nw_faces):
        return False  # duplicate non-wild faces -straight impossible
    for start in range(10):
        window = [(start + i) % 13 for i in range(5)]
        needed = sum(1 for f in window if f not in unique)
        if needed <= wilds:
            return True
    return False


def evaluate(hand: list[int]) -> tuple[str, int]:
    """Score a five-card hand and return the hand name and payout multiplier.

    Builds suit_checker and face_checker from the five card indices, then
    tests hands from highest to lowest value.

    Args:
        hand: List of exactly five card indices (each 0-51).

    Returns:
        A (hand_name, payout_multiplier) tuple. Multiply payout_multiplier
        by the player's bet to get the actual coins won. Returns
        ("No Win", 0) when no qualifying hand is present.

    Raises:
        ValueError: If hand does not contain exactly 5 cards, or any
                    card index is outside 0-51.
    """
    if len(hand) != 5:
        raise ValueError(f"Hand must contain exactly 5 cards, got {len(hand)}")

    suit_checker = [0] * 4
    face_checker = [0] * 13

    for card in hand:
        if not (0 <= card <= 51):
            raise ValueError(f"Invalid card index: {card}")
        suit_checker[card // 13] += 1
        face_checker[card % 13] += 1

    flush = _is_flush(suit_checker)
    straight = _is_straight(face_checker)

    # Royal Flush: ace-high straight flush (Ten through Ace, same suit)
    if flush and straight and face_checker[0] == 1 and face_checker[9] == 1:
        return ("Royal Flush", PAYOUTS["Royal Flush"])

    if flush and straight:
        return ("Straight Flush", PAYOUTS["Straight Flush"])

    if 4 in face_checker:
        return ("Four of a Kind", PAYOUTS["Four of a Kind"])

    if 3 in face_checker and 2 in face_checker:
        return ("Full House", PAYOUTS["Full House"])

    if flush:
        return ("Flush", PAYOUTS["Flush"])

    if straight:
        return ("Straight", PAYOUTS["Straight"])

    if 3 in face_checker:
        return ("Three of a Kind", PAYOUTS["Three of a Kind"])

    pairs = face_checker.count(2)

    if pairs == 2:
        return ("Two Pair", PAYOUTS["Two Pair"])

    if pairs == 1:
        for idx in _JACKS_OR_BETTER:
            if face_checker[idx] == 2:
                return ("Pair of Jacks or Better", PAYOUTS["Pair of Jacks or Better"])

    return ("No Win", PAYOUTS["No Win"])


def evaluate_deuces_wild(hand: list[int]) -> tuple[str, int]:
    """Score a hand with Twos (face index 1) as wild cards.

    Wild cards substitute for any card to form the best possible hand.
    Five of a Kind (5,000 coins) is achievable when wilds fill the gap.

    Args:
        hand: List of exactly five card indices (each 0-51).

    Returns:
        A (hand_name, payout_multiplier) tuple using PAYOUTS_DW.

    Raises:
        ValueError: Same conditions as evaluate().
    """
    if len(hand) != 5:
        raise ValueError(f"Hand must contain exactly 5 cards, got {len(hand)}")

    suit_checker = [0] * 4
    face_checker = [0] * 13

    for card in hand:
        if not (0 <= card <= 51):
            raise ValueError(f"Invalid card index: {card}")
        suit_checker[card // 13] += 1
        face_checker[card % 13] += 1

    wilds = face_checker[1]  # Twos are wild

    # Non-wild card properties
    nw_faces = [c % 13 for c in hand if c % 13 != 1]
    nw_suits = [c // 13 for c in hand if c % 13 != 1]

    nw_face_counts = [0] * 13
    for f in nw_faces:
        nw_face_counts[f] += 1
    max_nw = max(nw_face_counts) if nw_faces else 0

    # 1. Five of a Kind -all non-wilds share exactly one face value
    if len(set(nw_faces)) <= 1:
        return ("Five of a Kind", PAYOUTS_DW["Five of a Kind"])

    # 2. Flush / Straight -checked before Four of a Kind because
    #    Royal/Straight Flush outranks it (e.g., suited T-J-Q-K + wild = RF)
    flush = len(set(nw_suits)) <= 1 if nw_suits else True
    straight = _is_straight_wild(nw_faces, wilds)

    if flush and straight:
        nw_set = set(nw_faces)
        if nw_set <= _ROYAL_FACES and len(_ROYAL_FACES - nw_set) <= wilds:
            return ("Royal Flush", PAYOUTS_DW["Royal Flush"])
        return ("Straight Flush", PAYOUTS_DW["Straight Flush"])

    # 3. Four of a Kind
    if max_nw + wilds >= 4:
        return ("Four of a Kind", PAYOUTS_DW["Four of a Kind"])

    # 4. Full House
    nw_pairs = sum(1 for c in nw_face_counts if c == 2)
    nw_trips = sum(1 for c in nw_face_counts if c == 3)
    if wilds == 0 and nw_trips == 1 and nw_pairs == 1:
        return ("Full House", PAYOUTS_DW["Full House"])
    if wilds == 1 and nw_pairs == 2:
        # Two non-wild pairs + 1 wild ->best use is triple one pair ->3+2
        return ("Full House", PAYOUTS_DW["Full House"])

    # 5-6. Flush / Straight alone
    if flush:
        return ("Flush", PAYOUTS_DW["Flush"])
    if straight:
        return ("Straight", PAYOUTS_DW["Straight"])

    # 7. Three of a Kind
    if max_nw + wilds >= 3:
        return ("Three of a Kind", PAYOUTS_DW["Three of a Kind"])

    # 8-9. Two Pair / Pair / No Win (only reachable with wilds == 0 or 1)
    if wilds == 0:
        pairs_count = face_checker.count(2)
        if pairs_count == 2:
            return ("Two Pair", PAYOUTS_DW["Two Pair"])
        if pairs_count == 1:
            for idx in _JACKS_OR_BETTER:
                if face_checker[idx] == 2:
                    return (
                        "Pair of Jacks or Better",
                        PAYOUTS_DW["Pair of Jacks or Better"],
                    )
        return ("No Win", PAYOUTS_DW["No Win"])

    # wilds == 1, max_nw == 1 (all non-wilds distinct; Three of a Kind ruled out)
    # Wild always pairs with the best non-wild face available, at minimum as Ace.
    return ("Pair of Jacks or Better", PAYOUTS_DW["Pair of Jacks or Better"])
