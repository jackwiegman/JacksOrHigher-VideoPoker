"""
Unit tests for the scorer module.

Each test uses concrete card indices so the hand is unambiguous.
Card index encoding:
  index // 13 -> suit  (0=Spades, 1=Diamonds, 2=Clubs, 3=Hearts)
  index % 13  -> face  (0=Ace, 1=Two, ..., 9=Ten, 10=Jack, 11=Queen, 12=King)

Quick reference (Spades = 0-12, Diamonds = 13-25, Clubs = 26-38, Hearts = 39-51):
  0=A  9=10  10=J  11=Q  12=K  (Spades)
  13=A 22=10 23=J  24=Q  25=K  (Diamonds)
  26=A 35=10 36=J  37=Q  38=K  (Clubs)
  39=A 48=10 49=J  50=Q  51=K  (Hearts)

Author: Jack Wiegman
"""

import unittest
from scorer import evaluate, evaluate_deuces_wild, PAYOUTS, PAYOUTS_DW


class TestRoyalFlush(unittest.TestCase):

    def test_royal_flush_spades(self):
        # A(S) 10(S) J(S) Q(S) K(S)
        hand = [0, 9, 10, 11, 12]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Royal Flush")
        self.assertEqual(payout, 2000)

    def test_royal_flush_hearts(self):
        # A(H) 10(H) J(H) Q(H) K(H)
        hand = [39, 48, 49, 50, 51]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Royal Flush")
        self.assertEqual(payout, 2000)


class TestStraightFlush(unittest.TestCase):

    def test_straight_flush_low(self):
        # 3(S) 4(S) 5(S) 6(S) 7(S)  (not ace-high ->not royal)
        hand = [2, 3, 4, 5, 6]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Straight Flush")
        self.assertEqual(payout, 250)

    def test_straight_flush_ace_low(self):
        # A(S) 2(S) 3(S) 4(S) 5(S)  (ace-low straight flush ->not royal)
        hand = [0, 1, 2, 3, 4]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Straight Flush")
        self.assertEqual(payout, 250)


class TestFourOfAKind(unittest.TestCase):

    def test_four_aces(self):
        # A(S) A(D) A(C) A(H) 2(S)
        hand = [0, 13, 26, 39, 1]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Four of a Kind")
        self.assertEqual(payout, 125)

    def test_four_kings(self):
        # K(S) K(D) K(C) K(H) 2(S)
        hand = [12, 25, 38, 51, 1]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Four of a Kind")
        self.assertEqual(payout, 125)


class TestFullHouse(unittest.TestCase):

    def test_three_aces_two_kings(self):
        # A(S) A(D) A(C) K(S) K(D)
        hand = [0, 13, 26, 12, 25]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Full House")
        self.assertEqual(payout, 40)

    def test_three_twos_two_threes(self):
        # 2(S) 2(D) 2(C) 3(S) 3(D)
        hand = [1, 14, 27, 2, 15]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Full House")
        self.assertEqual(payout, 40)


class TestFlush(unittest.TestCase):

    def test_flush_non_straight(self):
        # A(S) 3(S) 5(S) 7(S) 9(S)  (every-other rank, not consecutive)
        hand = [0, 2, 4, 6, 8]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Flush")
        self.assertEqual(payout, 25)

    def test_flush_diamonds(self):
        # A(D) 3(D) 5(D) 7(D) 9(D)
        hand = [13, 15, 17, 19, 21]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Flush")
        self.assertEqual(payout, 25)


class TestStraight(unittest.TestCase):

    def test_straight_mixed_suits(self):
        # 3(S) 4(D) 5(C) 6(H) 7(S)  (mixed suits, consecutive ranks)
        hand = [2, 16, 30, 44, 6]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Straight")
        self.assertEqual(payout, 20)

    def test_ace_low_straight_mixed(self):
        # A(S) 2(D) 3(C) 4(H) 5(S)
        hand = [0, 14, 28, 42, 4]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Straight")
        self.assertEqual(payout, 20)

    def test_ace_high_straight_mixed(self):
        # 10(S) J(D) Q(C) K(H) A(S)
        hand = [9, 23, 37, 51, 0]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Straight")
        self.assertEqual(payout, 20)


class TestThreeOfAKind(unittest.TestCase):

    def test_three_aces(self):
        # A(S) A(D) A(C) 2(S) 3(S)
        hand = [0, 13, 26, 1, 2]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Three of a Kind")
        self.assertEqual(payout, 15)


class TestTwoPair(unittest.TestCase):

    def test_aces_and_kings(self):
        # A(S) A(D) K(S) K(D) 2(S)
        hand = [0, 13, 12, 25, 1]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Two Pair")
        self.assertEqual(payout, 10)

    def test_two_low_pairs(self):
        # 2(S) 2(D) 3(S) 3(D) 4(S)
        hand = [1, 14, 2, 15, 3]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Two Pair")
        self.assertEqual(payout, 10)


class TestPairJacksOrBetter(unittest.TestCase):

    def test_pair_of_jacks(self):
        # J(S) J(D) 2(S) 3(S) 4(S)
        hand = [10, 23, 1, 2, 3]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Pair of Jacks or Better")
        self.assertEqual(payout, 5)

    def test_pair_of_queens(self):
        # Q(S) Q(D) 2(S) 3(S) 4(S)
        hand = [11, 24, 1, 2, 3]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Pair of Jacks or Better")
        self.assertEqual(payout, 5)

    def test_pair_of_kings(self):
        # K(S) K(D) 2(S) 3(S) 4(S)
        hand = [12, 25, 1, 2, 3]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Pair of Jacks or Better")
        self.assertEqual(payout, 5)

    def test_pair_of_aces(self):
        # A(S) A(D) 2(S) 3(S) 4(S)
        hand = [0, 13, 1, 2, 3]
        name, payout = evaluate(hand)
        self.assertEqual(name, "Pair of Jacks or Better")
        self.assertEqual(payout, 5)


class TestNoWin(unittest.TestCase):

    def test_pair_of_tens(self):
        # 10(S) 10(D) 2(S) 3(S) 4(S)  (Tens do not qualify as Jacks or Better)
        hand = [9, 22, 1, 2, 3]
        name, payout = evaluate(hand)
        self.assertEqual(name, "No Win")
        self.assertEqual(payout, 0)

    def test_pair_of_nines(self):
        # 9(S) 9(D) 2(S) 3(S) 4(S)
        hand = [8, 21, 1, 2, 3]
        name, payout = evaluate(hand)
        self.assertEqual(name, "No Win")
        self.assertEqual(payout, 0)

    def test_no_pair_garbage(self):
        # A(S) 3(D) 5(C) 7(H) 9(S)  (no pair, no straight, no flush)
        hand = [0, 15, 30, 45, 8]
        name, payout = evaluate(hand)
        self.assertEqual(name, "No Win")
        self.assertEqual(payout, 0)


class TestValidation(unittest.TestCase):

    def test_too_few_cards(self):
        with self.assertRaises(ValueError):
            evaluate([0, 1, 2, 3])

    def test_too_many_cards(self):
        with self.assertRaises(ValueError):
            evaluate([0, 1, 2, 3, 4, 5])

    def test_index_too_low(self):
        with self.assertRaises(ValueError):
            evaluate([-1, 1, 2, 3, 4])

    def test_index_too_high(self):
        with self.assertRaises(ValueError):
            evaluate([0, 1, 2, 3, 52])


class TestPayoutsDict(unittest.TestCase):

    def test_all_hands_present(self):
        expected = {
            "Royal Flush",
            "Straight Flush",
            "Four of a Kind",
            "Full House",
            "Flush",
            "Straight",
            "Three of a Kind",
            "Two Pair",
            "Pair of Jacks or Better",
            "No Win",
        }
        self.assertEqual(set(PAYOUTS.keys()), expected)

    def test_payouts_are_nonnegative(self):
        for name, coins in PAYOUTS.items():
            self.assertGreaterEqual(coins, 0, f"{name} payout is negative")

    def test_royal_flush_is_highest(self):
        self.assertEqual(max(PAYOUTS.values()), PAYOUTS["Royal Flush"])


# Deuces Wild tests
# Wild card is face index 1 (Two).  Quick ref:
#   1=2(S)  14=2(D)  27=2(C)  40=2(H)
# All other indices follow the same encoding as above.


class TestDeucesWildFiveOfAKind(unittest.TestCase):

    def test_four_aces_one_wild(self):
        # A(S) A(D) A(C) A(H) 2(S) ->Five Aces
        hand = [0, 13, 26, 39, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Five of a Kind")
        self.assertEqual(payout, 5000)

    def test_three_kings_two_wilds(self):
        # K(S) K(D) K(C) 2(D) 2(C) ->Five Kings
        hand = [12, 25, 38, 14, 27]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Five of a Kind")
        self.assertEqual(payout, 5000)

    def test_four_wilds_one_card(self):
        # A(S) 2(S) 2(D) 2(C) 2(H)  (requires 2+ decks in practice; valid indices)
        hand = [0, 1, 14, 27, 40]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Five of a Kind")
        self.assertEqual(payout, 5000)


class TestDeucesWildRoyalFlush(unittest.TestCase):

    def test_four_royals_one_wild_same_suit(self):
        # 10(S) J(S) Q(S) K(S) 2(S) ->wild becomes A(S) ->Royal Flush
        hand = [9, 10, 11, 12, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Royal Flush")
        self.assertEqual(payout, 2000)

    def test_natural_royal_flush(self):
        # A(H) 10(H) J(H) Q(H) K(H) -no wilds
        hand = [39, 48, 49, 50, 51]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Royal Flush")
        self.assertEqual(payout, 2000)

    def test_rf_beats_four_of_a_kind(self):
        # Verify RF (same suit T-J-Q-K + wild) outranks FoaK in evaluation order
        hand = [9, 10, 11, 12, 1]  # 10(S) J(S) Q(S) K(S) 2(S)
        name, _ = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Royal Flush")  # not Four of a Kind


class TestDeucesWildStraightFlush(unittest.TestCase):

    def test_straight_flush_with_wild(self):
        # 3(S) 4(S) 5(S) 6(S) 2(S) ->wild becomes 7(S) ->3-7 SF
        hand = [2, 3, 4, 5, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Straight Flush")
        self.assertEqual(payout, 250)

    def test_natural_straight_flush(self):
        # 3(D) 4(D) 5(D) 6(D) 7(D) -no wilds
        hand = [15, 16, 17, 18, 19]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Straight Flush")
        self.assertEqual(payout, 250)


class TestDeucesWildFourOfAKind(unittest.TestCase):

    def test_three_kings_wild_kicker(self):
        # K(S) K(D) K(C) 2(S) A(H) ->wild becomes K(H) ->Four Kings
        hand = [12, 25, 38, 1, 39]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Four of a Kind")
        self.assertEqual(payout, 125)

    def test_pair_two_wilds(self):
        # A(S) A(D) 2(S) 2(D) 3(C) ->two wilds + pair Aces ->Four Aces
        hand = [0, 13, 1, 14, 28]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Four of a Kind")
        self.assertEqual(payout, 125)


class TestDeucesWildFullHouse(unittest.TestCase):

    def test_two_pairs_one_wild(self):
        # A(S) A(D) K(S) K(D) 2(S) ->two pairs + wild ->FH
        hand = [0, 13, 12, 25, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Full House")
        self.assertEqual(payout, 40)

    def test_natural_full_house(self):
        # A(S) A(D) A(C) K(S) K(D) -no wilds
        hand = [0, 13, 26, 12, 25]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Full House")
        self.assertEqual(payout, 40)


class TestDeucesWildFlush(unittest.TestCase):

    def test_flush_with_wild(self):
        # A(S) 3(S) 5(S) 7(S) 2(S) -all Spades, wild can't make a straight ->Flush
        hand = [0, 2, 4, 6, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Flush")
        self.assertEqual(payout, 25)

    def test_natural_flush(self):
        # A(D) 3(D) 5(D) 7(D) 9(D) -no wilds
        hand = [13, 15, 17, 19, 21]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Flush")
        self.assertEqual(payout, 25)


class TestDeucesWildStraight(unittest.TestCase):

    def test_straight_with_wild_mixed_suits(self):
        # 3(S) 4(D) 6(C) 7(H) 2(S) ->wild becomes 5 ->3-7 Straight
        hand = [2, 16, 31, 45, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Straight")
        self.assertEqual(payout, 20)

    def test_natural_straight(self):
        # 3(S) 4(D) 5(C) 6(H) 7(S) -no wilds
        hand = [2, 16, 30, 44, 6]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Straight")
        self.assertEqual(payout, 20)


class TestDeucesWildThreeOfAKind(unittest.TestCase):

    def test_pair_plus_wild(self):
        # A(S) A(D) 3(S) 4(D) 2(S) ->wild becomes A ->Three Aces
        hand = [0, 13, 2, 16, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Three of a Kind")
        self.assertEqual(payout, 15)


class TestDeucesWildTwoPair(unittest.TestCase):

    def test_natural_two_pair(self):
        # A(S) A(D) K(S) K(D) 3(S) -no wilds
        hand = [0, 13, 12, 25, 2]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Two Pair")
        self.assertEqual(payout, 10)


class TestDeucesWildPairJB(unittest.TestCase):

    def test_natural_pair_aces(self):
        # A(S) A(D) 3(S) 4(S) 5(S) -no wilds
        hand = [0, 13, 2, 3, 4]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Pair of Jacks or Better")
        self.assertEqual(payout, 5)

    def test_one_wild_low_cards(self):
        # 3(S) 5(D) 7(C) 9(H) 2(S) ->wild becomes Ace ->Pair of JB
        hand = [2, 17, 32, 47, 1]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "Pair of Jacks or Better")
        self.assertEqual(payout, 5)


class TestDeucesWildNoWin(unittest.TestCase):

    def test_no_pair_no_wild(self):
        # A(S) 3(D) 5(C) 7(H) 9(S) -no wilds, no pair, no flush, no straight
        hand = [0, 15, 30, 45, 8]
        name, payout = evaluate_deuces_wild(hand)
        self.assertEqual(name, "No Win")
        self.assertEqual(payout, 0)


class TestDeucesWildPayoutsMeta(unittest.TestCase):

    def test_five_of_a_kind_is_highest(self):
        self.assertEqual(max(PAYOUTS_DW.values()), PAYOUTS_DW["Five of a Kind"])

    def test_five_of_a_kind_beats_royal(self):
        self.assertGreater(PAYOUTS_DW["Five of a Kind"], PAYOUTS_DW["Royal Flush"])

    def test_all_hands_present(self):
        expected = {
            "Five of a Kind",
            "Royal Flush",
            "Straight Flush",
            "Four of a Kind",
            "Full House",
            "Flush",
            "Straight",
            "Three of a Kind",
            "Two Pair",
            "Pair of Jacks or Better",
            "No Win",
        }
        self.assertEqual(set(PAYOUTS_DW.keys()), expected)


class TestDeucesWildValidation(unittest.TestCase):

    def test_too_few_cards(self):
        with self.assertRaises(ValueError):
            evaluate_deuces_wild([0, 1, 2, 3])

    def test_too_many_cards(self):
        with self.assertRaises(ValueError):
            evaluate_deuces_wild([0, 1, 2, 3, 4, 5])

    def test_bad_index(self):
        with self.assertRaises(ValueError):
            evaluate_deuces_wild([0, 1, 2, 3, 52])


if __name__ == "__main__":
    unittest.main(verbosity=2)
