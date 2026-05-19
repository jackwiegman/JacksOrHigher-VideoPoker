"""
Unit tests for the Player class.

Author: Jack Wiegman
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from player import Player


class TestPlayerInit(unittest.TestCase):

    def test_name(self):
        p = Player("Alice")
        self.assertEqual(p.name, "Alice")

    def test_bank_starts_at_zero(self):
        p = Player("Alice")
        self.assertEqual(p.bank, 0.0)


class TestBankProperty(unittest.TestCase):

    def setUp(self) -> None:
        self.player = Player("TestUser")

    def test_set_valid_balance(self):
        self.player.bank = 100.0
        self.assertEqual(self.player.bank, 100.0)

    def test_set_zero_balance(self):
        self.player.bank = 0.0
        self.assertEqual(self.player.bank, 0.0)

    def test_set_negative_raises(self):
        with self.assertRaises(ValueError):
            self.player.bank = -1.0


class TestAddFunds(unittest.TestCase):

    def setUp(self) -> None:
        self.player = Player("TestUser")

    def test_add_positive_coins(self):
        self.player.add_funds(50)
        self.assertEqual(self.player.bank, 50.0)

    def test_add_accumulates(self):
        self.player.add_funds(30)
        self.player.add_funds(20)
        self.assertEqual(self.player.bank, 50.0)

    def test_add_zero_raises(self):
        with self.assertRaises(ValueError):
            self.player.add_funds(0)

    def test_add_negative_raises(self):
        with self.assertRaises(ValueError):
            self.player.add_funds(-10)


class TestPersistence(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch("player.SAVES_DIR", Path(self.temp_dir))
        self.patcher.start()
        self.player = Player("TestUser")

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_load_returns_false_for_new_player(self):
        self.assertFalse(self.player.load())

    def test_bank_unchanged_when_no_save_file(self):
        self.player.load()
        self.assertEqual(self.player.bank, 0.0)

    def test_save_creates_file(self):
        self.player.bank = 200.0
        self.player.save()
        save_file = Path(self.temp_dir) / "TestUser.txt"
        self.assertTrue(save_file.exists())

    def test_save_and_load_round_trip(self):
        self.player.bank = 250.0
        self.player.save()
        p2 = Player("TestUser")
        result = p2.load()
        self.assertTrue(result)
        self.assertEqual(p2.bank, 250.0)

    def test_load_returns_true_for_existing_player(self):
        self.player.bank = 100.0
        self.player.save()
        self.assertTrue(self.player.load())
        self.assertEqual(self.player.bank, 100.0)

    def test_save_overwrites_previous(self):
        self.player.bank = 100.0
        self.player.save()
        self.player.bank = 999.0
        self.player.save()
        p2 = Player("TestUser")
        p2.load()
        self.assertEqual(p2.bank, 999.0)

    def test_corrupted_save_raises(self):
        save_file = Path(self.temp_dir) / "TestUser.txt"
        save_file.write_text("not_a_number")
        with self.assertRaises(ValueError):
            self.player.load()

    def test_save_creates_directory_if_missing(self):
        import shutil

        # Remove the temp dir to simulate missing game_saves/
        shutil.rmtree(self.temp_dir)
        self.player.bank = 50.0
        self.player.save()  # Should recreate dir without error
        p2 = Player("TestUser")
        p2.load()
        self.assertEqual(p2.bank, 50.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
