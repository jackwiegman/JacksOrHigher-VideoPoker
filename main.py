"""
Main entry point for Jacks or Better Video Poker.

Initializes the Tkinter root window and launches the VideoPokerApp.

Version: Final Project
Author: Jack Wiegman
Date: 2026-05-08
"""

import tkinter as tk
from app import VideoPokerApp


def main() -> None:
    root = tk.Tk()
    app = VideoPokerApp(root)
    app.run()


if __name__ == "__main__":
    main()
