"""
Unit tests for the Deck class.

Author: Jack Wiegman
"""

import unittest
from deck import Deck, CARD_BACK


class TestDeckInit(unittest.TestCase):

    def test_single_deck_defaults(self):
        d = Deck(1)
        self.assertEqual(d.num_decks, 1)
        self.assertEqual(d.total_cards, 52)
        self.assertEqual(d.cards_dealt, 0)

    def test_multi_deck_total(self):
        d = Deck(3)
        self.assertEqual(d.total_cards, 156)

    def test_max_decks(self):
        d = Deck(10)
        self.assertEqual(d.total_cards, 520)

    def test_num_decks_too_low(self):
        with self.assertRaises(ValueError):
            Deck(0)

    def test_num_decks_too_high(self):
        with self.assertRaises(ValueError):
            Deck(11)


class TestDeckDeal(unittest.TestCase):

    def setUp(self):
        # Use a large shoe so we don't hit the 60% reshuffle threshold
        # during the test runs (10 decks = 520 cards; 60% = 312 deals)
        self.deck = Deck(10)

    def test_deal_returns_valid_index(self):
        for _ in range(20):
            idx = self.deck.deal_card()
            self.assertGreaterEqual(idx, 0)
            self.assertLessEqual(idx, 51)

    def test_deal_increments_cards_dealt(self):
        self.deck.deal_card()
        self.assertEqual(self.deck.cards_dealt, 1)
        self.deck.deal_card()
        self.assertEqual(self.deck.cards_dealt, 2)

    def test_deal_each_card_limited_by_num_decks(self):
        # With a 1-deck shoe: each card may only be dealt once.
        # Deal all 52 cards and confirm no index appears more than once.
        d = Deck(1)
        seen: list[int] = []
        # Deal exactly 31 cards (< 60% of 52 = 31.2) before reshuffle kicks in
        for _ in range(31):
            seen.append(d.deal_card())
        self.assertEqual(
            len(seen), len(set(seen)), "Duplicate card dealt from single deck"
        )


class TestDeckReshuffle(unittest.TestCase):

    def test_reshuffle_resets_cards_dealt(self):
        d = Deck(1)
        for _ in range(5):
            d.deal_card()
        self.assertEqual(d.cards_dealt, 5)
        d.reshuffle()
        self.assertEqual(d.cards_dealt, 0)

    def test_reshuffle_allows_dealing_again(self):
        d = Deck(1)
        for _ in range(31):  # just under 60% of 52
            d.deal_card()
        d.reshuffle()
        # Should be able to deal 31 more without error
        for _ in range(31):
            idx = d.deal_card()
            self.assertGreaterEqual(idx, 0)
            self.assertLessEqual(idx, 51)


class TestShouldReshuffle(unittest.TestCase):

    def test_false_initially(self):
        self.assertFalse(Deck(1).should_reshuffle)

    def test_false_below_threshold(self):
        d = Deck(10)  # 520 total; 60% = 312
        for _ in range(311):
            d.deal_card()
        self.assertFalse(d.should_reshuffle)

    def test_true_at_threshold(self):
        d = Deck(10)
        for _ in range(312):
            d.deal_card()
        self.assertTrue(d.should_reshuffle)

    def test_false_after_reshuffle(self):
        d = Deck(10)
        for _ in range(312):
            d.deal_card()
        d.reshuffle()
        self.assertFalse(d.should_reshuffle)


class TestImageFor(unittest.TestCase):

    def setUp(self) -> None:
        self.deck = Deck(1)

    def test_ace_of_spades_index_0(self):
        img = self.deck.image_for(0)
        self.assertIn("Ace_of_Spades", img)

    def test_ace_of_diamonds_index_13(self):
        img = self.deck.image_for(13)
        self.assertIn("Ace_of_Diamonds", img)

    def test_ace_of_clubs_index_26(self):
        img = self.deck.image_for(26)
        self.assertIn("Ace_of_Clubs", img)

    def test_ace_of_hearts_index_39(self):
        img = self.deck.image_for(39)
        self.assertIn("Ace_of_Hearts", img)

    def test_king_of_hearts_index_51(self):
        img = self.deck.image_for(51)
        self.assertIn("King_of_Hearts", img)

    def test_invalid_index_negative(self):
        with self.assertRaises(ValueError):
            self.deck.image_for(-1)

    def test_invalid_index_too_large(self):
        with self.assertRaises(ValueError):
            self.deck.image_for(52)

    def test_card_back_constant_defined(self):
        self.assertIn("Yellow_back", CARD_BACK)


if __name__ == "__main__":
    unittest.main(verbosity=2)
