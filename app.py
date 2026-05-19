"""
VideoPokerApp - Tkinter GUI for Jacks or Better Video Poker.

Handles the full game loop including startup popups, betting, dealing,
card animation, scoring, and bank persistence.

Version: Final Project
Author: Jack Wiegman
Date: 2026-05-08
"""

import tkinter as tk
from tkinter import ttk, messagebox

import pythonGraph as pg

from deck import Deck, ASSETS_DIR
from scorer import evaluate, evaluate_deuces_wild, PAYOUTS, PAYOUTS_DW
from player import Player

# Sound asset paths
WON_SOUND = str(ASSETS_DIR / "won.wav")
LOST_SOUND = str(ASSETS_DIR / "lost.mp3")

# Layout and style constants

CARD_W, CARD_H = 100, 140  # displayed card size (2x the native 50x70 GIFs)
CARD_XPAD = 8  # horizontal gap between card columns
DEAL_DELAY_MS = 350  # ms between each card flip during animation

BG = "#076324"  # casino green
BTN_GOLD = "#c8a84b"  # control button face
BTN_KEEP = "#2e7d32"  # keep button (dark green)
BTN_DISCARD = "#b71c1c"  # discard button (dark red)
BTN_WILD = "#e65100"  # wild card indicator (deep orange)
FG_WHITE = "white"
FG_GOLD = "gold"
FG_YELLOW = "#ffeb3b"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_INFO = ("Helvetica", 13)
FONT_BTN = ("Helvetica", 11, "bold")
FONT_KEEP = ("Helvetica", 10, "bold")
FONT_TINY = ("Courier", 8)

_PAYOUT_LINE = "RF:2000  SF:250  4K:125  FH:40  FL:25  ST:20  3K:15  2P:10  JB:5"
_PAYOUT_LINE_DW = (
    "5K:5000  RF:2000  SF:250  4K:125  FH:40  FL:25  ST:20  3K:15  2P:10  JB:5  ★2=WILD"
)

# Game states
_STARTUP = "STARTUP"
_BETTING = "BETTING"
_ANIMATING = "ANIMATING"
_DEALT = "DEALT"
_SCORING = "SCORING"


class VideoPokerApp:
    """Main Tkinter application for Jacks or Better / Deuces Wild Video Poker."""

    def __init__(self, root: tk.Tk) -> None:
        self.__root = root
        root.title("Jacks or Better — Video Poker")
        root.configure(bg=BG)
        root.resizable(False, False)

        # Game state
        self.__state: str = _STARTUP
        self.__player: Player | None = None
        self.__deck: Deck | None = None
        self.__hand: list[int] = []
        self.__kept: list[bool] = [True] * 5
        self.__bet: int = 0
        self.__deuces_wild: bool = False

        # Dynamic label text
        self.__bank_var = tk.StringVar(value="Bank: —")
        self.__bet_var = tk.StringVar(value="Bet: 0 coins")
        self.__result_var = tk.StringVar(value="Starting up…")
        self.__title_var = tk.StringVar(value="JACKS OR BETTER")
        self.__payout_var = tk.StringVar(value=_PAYOUT_LINE)

        # Image cache - PhotoImage refs must stay alive or Tk garbage collects them
        self.__img_cache: list[tk.PhotoImage] = []
        self.__back_photo: tk.PhotoImage | None = None
        self.__face_photos: list[tk.PhotoImage | None] = [None] * 5

        # Widget references (populated by _build_ui)
        self.__card_labels: list[tk.Label] = []
        self.__keep_btns: list[tk.Button] = []
        self.__bet_btns: list[tk.Button] = []  # Bet One, Bet Amount, All In
        self.__btn_deal: tk.Button  # assigned in _build_ui

        self.__back_photo = self._make_card_back()
        self._build_ui()
        self.__root.after(100, self._startup)

    # -------------------------------------------------------------------------
    # Image helpers
    # -------------------------------------------------------------------------
    def _make_card_back(self) -> tk.PhotoImage:
        """Synthesise a card-back image - nested yellow/navy rectangles."""
        img = tk.PhotoImage(width=CARD_W, height=CARD_H)
        img.put("yellow", to=(0, 0, CARD_W, CARD_H))
        img.put("#1a237e", to=(4, 4, CARD_W - 4, CARD_H - 4))
        img.put("yellow", to=(9, 9, CARD_W - 9, CARD_H - 9))
        img.put("#1a237e", to=(14, 14, CARD_W - 14, CARD_H - 14))
        img.put("yellow", to=(19, 19, CARD_W - 19, CARD_H - 19))
        self.__img_cache.append(img)
        return img

    def _open_gif_photo(self, path: str) -> tk.PhotoImage:
        """Load a card GIF and zoom 2x (50x70 -> 100x140)."""
        raw = tk.PhotoImage(file=path)
        zoomed = raw.zoom(2, 2)
        self.__img_cache.extend([raw, zoomed])
        return zoomed

    # -------------------------------------------------------------------------
    # Widget construction
    # -------------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = self.__root

        # Title and result banner
        top = tk.Frame(root, bg=BG)
        top.pack(pady=(14, 0))
        tk.Label(
            top, textvariable=self.__title_var, font=FONT_TITLE, bg=BG, fg=FG_GOLD
        ).pack()
        tk.Label(
            top, textvariable=self.__result_var, font=FONT_INFO, bg=BG, fg=FG_WHITE
        ).pack(pady=(3, 0))

        tk.Label(
            root, textvariable=self.__payout_var, font=FONT_TINY, bg=BG, fg="#aaaaaa"
        ).pack(pady=(2, 0))

        # Card area
        cards_row = tk.Frame(root, bg=BG)
        cards_row.pack(pady=(10, 0))

        for i in range(5):
            col = tk.Frame(cards_row, bg=BG)
            col.grid(row=0, column=i, padx=CARD_XPAD)

            lbl = tk.Label(col, image=self.__back_photo, bg=BG, relief="flat")
            lbl.pack()
            self.__card_labels.append(lbl)

            btn = tk.Button(
                col,
                text="Keep",
                font=FONT_KEEP,
                bg=BTN_KEEP,
                fg=FG_WHITE,
                activebackground="#388e3c",
                activeforeground=FG_WHITE,
                width=8,
                relief="raised",
                cursor="hand2",
                state="disabled",
                command=lambda idx=i: self._toggle_keep(idx),
            )
            btn.pack(pady=(5, 0))
            self.__keep_btns.append(btn)

        # Info bar
        info = tk.Frame(root, bg=BG)
        info.pack(pady=8)
        tk.Label(
            info,
            textvariable=self.__bank_var,
            font=FONT_INFO,
            bg=BG,
            fg=FG_WHITE,
            width=26,
            anchor="e",
        ).grid(row=0, column=0, padx=16)
        tk.Label(
            info,
            textvariable=self.__bet_var,
            font=FONT_INFO,
            bg=BG,
            fg=FG_YELLOW,
            width=26,
            anchor="w",
        ).grid(row=0, column=1, padx=16)

        # Control buttons - all start disabled until startup finishes
        btn_row = tk.Frame(root, bg=BG)
        btn_row.pack(pady=(2, 16))

        btn_defs = [
            ("Bet\nOne Coin", self._on_bet_one, True),
            ("Bet\nAmount", self._on_bet_amount, True),
            ("All\nIn", self._on_all_in, True),
            ("Deal", self._on_deal, False),
            ("Exit", self._on_exit, False),
        ]
        for col_idx, (label, cmd, is_bet_btn) in enumerate(btn_defs):
            b = tk.Button(
                btn_row,
                text=label,
                command=cmd,
                font=FONT_BTN,
                bg=BTN_GOLD,
                fg="black",
                activebackground="#e8c860",
                width=9,
                height=2,
                relief="raised",
                cursor="hand2",
                state="disabled",
            )
            b.grid(row=0, column=col_idx, padx=5)
            if is_bet_btn:
                self.__bet_btns.append(b)
            if label == "Deal":
                self.__btn_deal = b

        # Exit is always available
        btn_row.grid_slaves(row=0, column=4)[0].configure(state="normal")

    # -------------------------------------------------------------------------
    # Card display helpers
    # -------------------------------------------------------------------------
    def _show_back(self, slot: int) -> None:
        self.__face_photos[slot] = None
        self.__card_labels[slot].configure(image=self.__back_photo)

    def _show_face(self, slot: int, card_index: int) -> None:
        photo = self._open_gif_photo(self.__deck.image_for(card_index))
        self.__face_photos[slot] = photo
        self.__card_labels[slot].configure(image=photo)

    def _show_all_backs(self) -> None:
        for i in range(5):
            self._show_back(i)

    # -------------------------------------------------------------------------
    # Keep / Discard helpers
    # -------------------------------------------------------------------------
    def _toggle_keep(self, idx: int) -> None:
        if self.__deuces_wild and self.__hand[idx] % 13 == 1:
            return  # wild Twos are always kept in Deuces Wild
        self.__kept[idx] = not self.__kept[idx]
        self._refresh_keep_btn(idx)

    def _refresh_keep_btn(self, idx: int) -> None:
        btn = self.__keep_btns[idx]
        # Wild card in DW mode takes priority over keep/discard styling
        if self.__deuces_wild and self.__hand and self.__hand[idx] % 13 == 1:
            btn.configure(
                text="★WILD", bg=BTN_WILD, activebackground="#bf360c", fg=FG_WHITE
            )
            return
        if self.__kept[idx]:
            btn.configure(
                text="Keep", bg=BTN_KEEP, activebackground="#388e3c", fg=FG_WHITE
            )
        else:
            btn.configure(
                text="Discard", bg=BTN_DISCARD, activebackground="#e53935", fg=FG_WHITE
            )

    def _reset_keeps(self) -> None:
        self.__kept = [True] * 5
        for i in range(5):
            self._refresh_keep_btn(i)

    def _set_keep_btns_state(self, state: str) -> None:
        for btn in self.__keep_btns:
            btn.configure(state=state)

    # -------------------------------------------------------------------------
    # Button state helpers
    # -------------------------------------------------------------------------
    def _set_betting_btns_state(self, state: str) -> None:
        for btn in self.__bet_btns:
            btn.configure(state=state)

    def _lock_ui(self) -> None:
        """Disable all interactive controls during animation."""
        self._set_keep_btns_state("disabled")
        self._set_betting_btns_state("disabled")
        self.__btn_deal.configure(state="disabled")

    def _unlock_for_betting(self) -> None:
        """Restore BETTING state: bet buttons + Deal active; Keep/Discard off."""
        self._set_keep_btns_state("disabled")
        self._set_betting_btns_state("normal")
        self.__btn_deal.configure(state="normal", text="Deal")

    def _unlock_for_draw(self) -> None:
        """Restore DEALT state: Keep/Discard + Draw active; bet buttons off."""
        self._set_keep_btns_state("normal")
        self._set_betting_btns_state("disabled")
        self.__btn_deal.configure(state="normal", text="Draw")

    # -------------------------------------------------------------------------
    # Label updaters
    # -------------------------------------------------------------------------
    def _refresh_bank_label(self) -> None:
        if self.__player:
            c = self.__player.bank
            self.__bank_var.set(f"Bank: {c:.0f} coins  (${c * 5:.2f})")

    def _refresh_bet_label(self) -> None:
        s = "coin" if self.__bet == 1 else "coins"
        self.__bet_var.set(f"Bet: {self.__bet} {s}")

    # -------------------------------------------------------------------------
    # Sound
    # -------------------------------------------------------------------------
    def _play_sound(self, path: str) -> None:
        """Play a sound file using pythonGraph."""
        pg.play_sound_effect(path)

    # -------------------------------------------------------------------------
    # Betting callbacks
    # -------------------------------------------------------------------------
    def _on_bet_one(self) -> None:
        if self.__state != _BETTING or self.__player is None:
            return
        if self.__player.bank <= 0:
            coins = self._ask_add_funds(self.__player.name, is_new=False)
            if coins > 0:
                self.__player.add_funds(coins)
                self.__player.save()
                self._refresh_bank_label()
            return
        if self.__bet >= 50:
            return
        self.__player.bank -= 1
        self.__bet += 1
        self._refresh_bank_label()
        self._refresh_bet_label()

    def _on_bet_amount(self) -> None:
        if self.__state != _BETTING or self.__player is None:
            return
        if self.__player.bank <= 0 and self.__bet == 0:
            coins = self._ask_add_funds(self.__player.name, is_new=False)
            if coins > 0:
                self.__player.add_funds(coins)
                self.__player.save()
                self._refresh_bank_label()
            return

        # Available coins = current bank + already-deducted bet (refundable)
        available = self.__player.bank + self.__bet
        max_bet = min(50, available)

        result: list[int] = []

        popup = tk.Toplevel(self.__root)
        popup.title("Bet Amount")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.transient(self.__root)
        popup.grab_set()

        tk.Label(
            popup, text="How many coins to bet?", font=FONT_INFO, bg=BG, fg=FG_WHITE
        ).pack(pady=(16, 4), padx=28)
        tk.Label(
            popup,
            text=f"(1 – {max_bet}  |  Bank: {self.__player.bank} coins)",
            font=FONT_TINY,
            bg=BG,
            fg="#aaaaaa",
        ).pack()

        spinbox = tk.Spinbox(
            popup, from_=1, to=max_bet, width=8, font=FONT_INFO, justify="center"
        )
        spinbox.delete(0, "end")
        spinbox.insert(0, str(self.__bet if 1 <= self.__bet <= max_bet else 1))
        spinbox.pack(padx=28, pady=(6, 4))

        err_var = tk.StringVar()
        tk.Label(
            popup, textvariable=err_var, font=FONT_TINY, bg=BG, fg="#ff6666"
        ).pack()

        def on_ok(_event=None) -> None:
            try:
                amount = int(spinbox.get())
                if not (1 <= amount <= max_bet):
                    raise ValueError
            except ValueError:
                err_var.set(f"Enter a whole number between 1 and {max_bet}.")
                return
            result.append(amount)
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        tk.Button(
            popup,
            text="Bet",
            command=on_ok,
            font=FONT_BTN,
            bg=BTN_GOLD,
            fg="black",
            activebackground="#e8c860",
            width=10,
            cursor="hand2",
        ).pack(pady=(4, 16))
        spinbox.bind("<Return>", on_ok)

        self._center_window(popup)
        self.__root.wait_window(popup)

        if not result:
            return

        new_bet = result[0]
        # Refund old bet, then deduct new bet
        self.__player.bank += self.__bet
        self.__player.bank -= new_bet
        self.__bet = new_bet
        self._refresh_bank_label()
        self._refresh_bet_label()

    def _on_all_in(self) -> None:
        if self.__state != _BETTING or self.__player is None:
            return
        if self.__player.bank <= 0 and self.__bet == 0:
            coins = self._ask_add_funds(self.__player.name, is_new=False)
            if coins > 0:
                self.__player.add_funds(coins)
                self.__player.save()
                self._refresh_bank_label()
            return
        # Refund current bet, then bet everything up to the 50-coin cap
        self.__player.bank += self.__bet
        add = min(self.__player.bank, 50)
        self.__player.bank -= add
        self.__bet = add
        self._refresh_bank_label()
        self._refresh_bet_label()

    def _on_exit(self) -> None:
        if self.__player:
            self.__player.save()
        self.__root.quit()

    # -------------------------------------------------------------------------
    # Game loop - Deal / Draw
    # -------------------------------------------------------------------------

    def _on_deal(self) -> None:
        """Handle Deal button press in both BETTING and DEALT states."""
        if self.__state == _BETTING:
            if self.__bet == 0:
                messagebox.showwarning(
                    "No Bet", "Place a bet first!", parent=self.__root
                )
                return
            self._begin_deal()

        elif self.__state == _DEALT:
            self._begin_draw()

    def _begin_deal(self) -> None:
        """Check reshuffle, deal 5 cards, start flip animation."""
        self.__state = _ANIMATING
        self._lock_ui()

        if self.__deck.should_reshuffle:
            self.__deck.reshuffle()
            self.__result_var.set("♻  Deck reshuffled — good luck!")
            self.__root.after(800, self._deal_cards)
        else:
            self._deal_cards()

    def _deal_cards(self) -> None:
        """Deal 5 card indices and launch the face-up animation."""
        self.__hand = [self.__deck.deal_card() for _ in range(5)]
        self._show_all_backs()
        self.__root.after(DEAL_DELAY_MS, lambda: self._flip_initial(0))

    def _flip_initial(self, slot: int) -> None:
        """Flip one card face-up; schedule the next, or finish when done."""
        if slot >= 5:
            self.__state = _DEALT
            self._reset_keeps()
            self._unlock_for_draw()
            mode = "Deuces Wild" if self.__deuces_wild else "Jacks or Better"
            self.__result_var.set(f"[{mode}]  Choose cards to keep, then press Draw")
            return
        self._show_face(slot, self.__hand[slot])
        self.__root.after(DEAL_DELAY_MS, lambda: self._flip_initial(slot + 1))

    def _begin_draw(self) -> None:
        """Replace discarded cards and start the draw animation."""
        self.__state = _SCORING
        self._lock_ui()

        replace = [i for i in range(5) if not self.__kept[i]]
        for i in replace:
            self.__hand[i] = self.__deck.deal_card()

        if replace:
            self.__root.after(DEAL_DELAY_MS, lambda: self._flip_draw(replace, 0))
        else:
            # All 5 kept - score immediately
            self.__root.after(200, self._finish_scoring)

    def _flip_draw(self, slots: list[int], idx: int) -> None:
        """Flip one replacement card; schedule the next, or score when done."""
        if idx >= len(slots):
            self._finish_scoring()
            return
        self._show_face(slots[idx], self.__hand[slots[idx]])
        self.__root.after(DEAL_DELAY_MS, lambda: self._flip_draw(slots, idx + 1))

    def _finish_scoring(self) -> None:
        """Evaluate the final hand, update the bank, and reset for next hand."""
        if self.__deuces_wild:
            hand_name, multiplier = evaluate_deuces_wild(self.__hand)
        else:
            hand_name, multiplier = evaluate(self.__hand)

        payout = multiplier * self.__bet

        self.__player.bank += payout
        self.__player.save()
        self._refresh_bank_label()

        # Result message + sound
        if payout > 0:
            net = payout - self.__bet
            sign = "+" if net >= 0 else ""
            self.__result_var.set(
                f"★ {hand_name}!   Payout: {payout} coins   ({sign}{net} net)"
            )
            self._play_sound(WON_SOUND)
        else:
            lost = self.__bet
            self.__result_var.set(
                f"No Win  —  {lost} coin{'s' if lost != 1 else ''} lost"
            )
            self._play_sound(LOST_SOUND)

        # Reshuffle check - notify if triggered for next hand
        reshuffle_pending = self.__deck.should_reshuffle

        # Reset for next hand
        self.__state = _BETTING
        self.__bet = 0
        self._refresh_bet_label()
        self._reset_keeps()
        self._set_keep_btns_state("disabled")
        self._unlock_for_betting()

        if reshuffle_pending:
            current = self.__result_var.get()
            self.__result_var.set(current + "   ♻ Reshuffle next hand")

    # -------------------------------------------------------------------------
    # Startup sequence
    # -------------------------------------------------------------------------

    def _center_window(self, win: tk.Toplevel) -> None:
        """Position a Toplevel centered over the main window."""
        win.update_idletasks()
        x = (
            self.__root.winfo_rootx()
            + (self.__root.winfo_width() - win.winfo_reqwidth()) // 2
        )
        y = (
            self.__root.winfo_rooty()
            + (self.__root.winfo_height() - win.winfo_reqheight()) // 2
        )
        win.geometry(f"+{x}+{y}")

    def _ask_name(self) -> str | None:
        """Modal popup: ask for the player's name."""
        result: list[str] = []

        popup = tk.Toplevel(self.__root)
        popup.title("Welcome")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.transient(self.__root)
        popup.grab_set()

        tk.Label(
            popup,
            text="♠  JACKS OR BETTER  ♠",
            font=("Helvetica", 14, "bold"),
            bg=BG,
            fg=FG_GOLD,
        ).pack(pady=(16, 4))
        tk.Label(
            popup, text="Enter your player name:", font=FONT_INFO, bg=BG, fg=FG_WHITE
        ).pack(pady=(4, 2))

        entry = tk.Entry(popup, font=FONT_INFO, width=22, justify="center")
        entry.pack(padx=24, pady=(0, 8))
        entry.focus_set()

        err_var = tk.StringVar()
        tk.Label(
            popup, textvariable=err_var, font=FONT_TINY, bg=BG, fg="#ff6666"
        ).pack()

        def on_ok(_event=None) -> None:
            name = entry.get().strip()
            if not name:
                err_var.set("Name cannot be empty.")
                return
            result.append(name)
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        tk.Button(
            popup,
            text="OK",
            command=on_ok,
            font=FONT_BTN,
            bg=BTN_GOLD,
            fg="black",
            activebackground="#e8c860",
            width=10,
            cursor="hand2",
        ).pack(pady=(4, 16))
        entry.bind("<Return>", on_ok)

        self._center_window(popup)
        self.__root.wait_window(popup)
        return result[0] if result else None

    def _ask_add_funds(self, player_name: str, is_new: bool = True) -> int:
        """Modal popup: ask how many coins to add to the bank.

        Used for new-player funding and mid-game bank=0 refills.
        Returns coins entered (>= 1), or 0 if dismissed.
        """
        result: list[int] = []

        popup = tk.Toplevel(self.__root)
        popup.title("Add Funds")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.transient(self.__root)
        popup.grab_set()

        greeting = (
            f"Welcome, {player_name}!\nYou need coins to play."
            if is_new
            else f"Bank is empty, {player_name}.\nAdd coins to continue."
        )
        tk.Label(
            popup, text=greeting, font=FONT_INFO, bg=BG, fg=FG_WHITE, justify="center"
        ).pack(pady=(16, 4), padx=24)
        tk.Label(
            popup, text="Each coin = $5.00", font=FONT_TINY, bg=BG, fg="#aaaaaa"
        ).pack()
        tk.Label(
            popup, text="How many coins?", font=FONT_INFO, bg=BG, fg=FG_YELLOW
        ).pack(pady=(8, 2))

        spinbox = tk.Spinbox(
            popup, from_=1, to=99999, width=10, font=FONT_INFO, justify="center"
        )
        spinbox.delete(0, "end")
        spinbox.insert(0, "100")
        spinbox.pack(padx=24, pady=(0, 6))

        err_var = tk.StringVar()
        tk.Label(
            popup, textvariable=err_var, font=FONT_TINY, bg=BG, fg="#ff6666"
        ).pack()

        def on_ok(_event=None) -> None:
            try:
                coins = int(spinbox.get())
                if coins < 1:
                    raise ValueError
            except ValueError:
                err_var.set("Please enter a whole number ≥ 1.")
                return
            result.append(coins)
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        tk.Button(
            popup,
            text="Add Funds",
            command=on_ok,
            font=FONT_BTN,
            bg=BTN_GOLD,
            fg="black",
            activebackground="#e8c860",
            width=12,
            cursor="hand2",
        ).pack(pady=(4, 16))
        spinbox.bind("<Return>", on_ok)

        self._center_window(popup)
        self.__root.wait_window(popup)
        return result[0] if result else 0

    def _ask_num_decks(self) -> int:
        """Modal popup: choose number of decks (1-10) via dropdown."""
        result: list[int] = [1]

        popup = tk.Toplevel(self.__root)
        popup.title("Game Setup")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.transient(self.__root)
        popup.grab_set()

        tk.Label(
            popup, text="How many decks?", font=FONT_INFO, bg=BG, fg=FG_WHITE
        ).pack(pady=(16, 6), padx=32)

        combo = ttk.Combobox(
            popup,
            values=[str(i) for i in range(1, 11)],
            state="readonly",
            width=6,
            font=FONT_INFO,
            justify="center",
        )
        combo.set("1")
        combo.pack(pady=(0, 8))

        tk.Label(
            popup,
            text="(Deck reshuffles after 60% dealt)",
            font=FONT_TINY,
            bg=BG,
            fg="#aaaaaa",
        ).pack()

        def on_ok(_event=None) -> None:
            result[0] = int(combo.get())
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        tk.Button(
            popup,
            text="Start Game",
            command=on_ok,
            font=FONT_BTN,
            bg=BTN_GOLD,
            fg="black",
            activebackground="#e8c860",
            width=12,
            cursor="hand2",
        ).pack(pady=(8, 16))
        combo.bind("<Return>", on_ok)

        self._center_window(popup)
        self.__root.wait_window(popup)
        return result[0]

    def _ask_variant(self) -> bool:
        """Modal popup: choose Jacks or Better vs Deuces Wild.

        Returns True if Deuces Wild was selected.
        """
        result: list[bool] = [False]

        popup = tk.Toplevel(self.__root)
        popup.title("Game Variant")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.transient(self.__root)
        popup.grab_set()

        tk.Label(
            popup, text="Choose your game variant:", font=FONT_INFO, bg=BG, fg=FG_WHITE
        ).pack(pady=(16, 10), padx=32)

        btn_frame = tk.Frame(popup, bg=BG)
        btn_frame.pack(padx=20, pady=(0, 4))

        def on_jb() -> None:
            result[0] = False
            popup.destroy()

        def on_dw() -> None:
            result[0] = True
            popup.destroy()

        tk.Button(
            btn_frame,
            text="♠  Jacks or Better",
            command=on_jb,
            font=FONT_BTN,
            bg=BTN_GOLD,
            fg="black",
            activebackground="#e8c860",
            width=18,
            height=2,
            cursor="hand2",
        ).grid(row=0, column=0, padx=8, pady=4)

        tk.Button(
            btn_frame,
            text="★  Deuces Wild",
            command=on_dw,
            font=FONT_BTN,
            bg="#8B0000",
            fg="white",
            activebackground="#a00000",
            width=18,
            height=2,
            cursor="hand2",
        ).grid(row=0, column=1, padx=8, pady=4)

        tk.Label(
            popup,
            text="Deuces Wild: all Twos are wild  |  Five of a Kind pays 5,000!",
            font=FONT_TINY,
            bg=BG,
            fg="#aaaaaa",
        ).pack(pady=(2, 16))

        popup.protocol("WM_DELETE_WINDOW", on_jb)  # default to JB if closed

        self._center_window(popup)
        self.__root.wait_window(popup)
        return result[0]

    def _startup(self) -> None:
        """Run the startup sequence: name -> fund bank -> variant -> deck count."""
        name = self._ask_name()
        if not name:
            self.__root.destroy()
            return

        player = Player(name)
        try:
            is_returning = player.load()
        except ValueError:
            messagebox.showerror(
                "Corrupted Save",
                f"Save file for '{name}' could not be read.\n"
                "Starting with a fresh bank.",
                parent=self.__root,
            )
            is_returning = False

        if not is_returning:
            coins = self._ask_add_funds(name, is_new=True)
            if coins <= 0:
                self.__root.destroy()
                return
            player.add_funds(coins)
            player.save()

        self.__player = player
        self._refresh_bank_label()
        self._refresh_bet_label()

        num_decks = self._ask_num_decks()
        self.__deck = Deck(num_decks)

        self.__deuces_wild = self._ask_variant()
        if self.__deuces_wild:
            self.__title_var.set("★  DEUCES WILD  ★")
            self.__payout_var.set(_PAYOUT_LINE_DW)
            self.__root.title(f"Deuces Wild — {name}")
        else:
            self.__root.title(f"Jacks or Better — {name}")

        # Hand off to gameplay
        self.__state = _BETTING
        self._unlock_for_betting()
        self.__result_var.set("Place your bet, then press Deal")

    # -------------------------------------------------------------------------
    # Entry point
    # -------------------------------------------------------------------------

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.__root.mainloop()
