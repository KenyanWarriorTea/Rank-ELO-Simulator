"""
Player model and storage helpers for Rank-ELO-Simulator.

Assumptions:
- rating_to_tier, TIERS, DIVISIONS live in src.ranks and are consistent with
  the rest of the codebase.
- Persistent storage is JSON file under data/players.json.

This file is written to be PEP8-compliant, typed and testable.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.ranks import rating_to_tier, TIERS, DIVISIONS  # local imports (project src root)


_MIN_RATING = 100.0
_DEFAULT_RATING = 1500.0


@dataclass
class Player:
    """Represents a single player and its state in the simulator."""

    id: int
    name: str
    rating: float = _DEFAULT_RATING
    win_streak: int = 0
    last_active: float = field(default_factory=lambda: time.time())
    history: List[Dict] = field(default_factory=list)
    tier: Dict = field(default_factory=lambda: rating_to_tier(_DEFAULT_RATING))

    # Placement / calibration
    placed: bool = False
    placement_games_played: int = 0
    placement_games_required: int = 0
    placement_wins: int = 0

    # LP / promo fields
    lp: int = 0
    in_promo: bool = False
    promo_games_left: int = 0
    promo_wins: int = 0
    promo_needed: int = 0

    wins: int = 0
    losses: int = 0

    def record_match(
        self,
        opponent_id: int,
        result: float,
        delta: float,
        lp_change: int = 0,
        placement: bool = False,
    ) -> None:
        """Record the outcome of a match.

        Args:
            opponent_id: id of the opponent.
            result: 1.0 for win, 0.5 draw, 0.0 loss.
            delta: rating delta applied to player rating.
            lp_change: LP (league points) change (int).
            placement: whether this match counts towards placement matches.
        """
        self.last_active = time.time()

        # streak tracking
        if result == 1.0:
            self.win_streak += 1
            self.wins += 1
        else:
            self.win_streak = 0
            if result == 0.0:
                self.losses += 1

        # rating change
        self.rating = max(_MIN_RATING, float(self.rating + delta))

        # LP handling (promo-aware)
        if lp_change != 0:
            self.apply_lp(lp_change)

        # placement logic
        if placement and not self.placed:
            self.placement_games_played += 1
            if result == 1.0:
                self.placement_wins += 1
            if self.placement_games_played >= self.placement_games_required:
                self.placed = True

        # update tier after rating change
        self.tier = rating_to_tier(self.rating)

        # append minimal history entry
        self.history.append(
            {
                "time": self.last_active,
                "opponent": opponent_id,
                "result": result,
                "delta": float(delta),
            }
        )

    def apply_lp(self, amount: int) -> None:
        """Apply LP to the player, handling promo series and carry-over.

        If not in promo and LP >= 100, the player enters promo and the
        excess LP is carried over as the new lp value after entry.
        """
        if self.in_promo:
            # Within promo: positive amount counts as a win for promo purposes.
            if amount > 0:
                self.promo_wins += 1
            self.promo_games_left = max(0, self.promo_games_left - 1)
            if self.promo_games_left == 0:
                self.resolve_promo()
            return

        self.lp += int(amount)
        if self.lp < 0:
            self.lp = 0

        if self.lp >= 100:
            extra = self.lp - 100
            # Enter promo (best of 3)
            self.enter_promo(best_of=3)
            # carry-over extra LP after entering promo
            self.lp = max(0, int(extra))

    def enter_promo(self, best_of: int = 3) -> None:
        """Begin a promotion series (best_of games)."""
        self.in_promo = True
        self.promo_games_left = int(best_of)
        self.promo_wins = 0
        self.promo_needed = (best_of // 2) + 1

    def resolve_promo(self) -> None:
        """Resolve promotion series and handle success / failure consequences."""
        success = self.promo_wins >= self.promo_needed
        # reset promo state
        self.in_promo = False
        self.promo_games_left = 0
        self.promo_wins = 0
        self.promo_needed = 0

        if success:
            self.promote_to_next_division()
            self.lp = 0
        else:
            # penalty for failing promo
            self.lp = max(0, self.lp - 50)
            self.rating = max(_MIN_RATING, float(self.rating - 10.0))

        self.tier = rating_to_tier(self.rating)

    def promote_to_next_division(self) -> None:
        """Promote the player to the next division or next tier if needed."""
        current_tier = self.tier.get("tier")
        current_div = self.tier.get("division")
        idx = next((i for i, t in enumerate(TIERS) if t[0] == current_tier), 0)

        try:
            div_idx = DIVISIONS.index(current_div)
        except ValueError:
            div_idx = len(DIVISIONS) - 1

        if div_idx > 0:
            # move to higher division within same tier
            new_div = DIVISIONS[div_idx - 1]
            new_tier = current_tier
            tier_min = TIERS[idx][1]
            if idx + 1 < len(TIERS):
                next_min = TIERS[idx + 1][1]
            else:
                next_min = tier_min + 300
            span = next_min - tier_min
            part = span / 4.0 if span > 0 else 1.0
            rev = DIVISIONS.index(new_div)
            new_rating = tier_min + part * (3 - rev) + 10
        else:
            # move to next tier, lowest division
            if idx + 1 < len(TIERS):
                new_tier = TIERS[idx + 1][0]
                new_div = DIVISIONS[-1]
                tier_min = TIERS[idx + 1][1]
                new_rating = tier_min + 10
            else:
                # already at top tier
                new_tier = current_tier
                new_div = current_div
                new_rating = float(self.rating + 30)

        self.rating = float(new_rating)
        self.tier = {"tier": new_tier, "division": new_div, "color": self.tier.get("color")}

    def apply_decay(self, decay_amount: float) -> None:
        """Apply rating decay while respecting minimum rating."""
        if decay_amount <= 0:
            return
        self.rating = max(_MIN_RATING, float(self.rating - float(decay_amount)))
        self.tier = rating_to_tier(self.rating)

    def to_dict(self) -> Dict:
        """Serialize player state to a JSON-serializable dict."""
        return {
            "id": int(self.id),
            "name": str(self.name),
            "rating": float(self.rating),
            "win_streak": int(self.win_streak),
            "last_active": float(self.last_active),
            "history": list(self.history),
            "tier": dict(self.tier),
            "placed": bool(self.placed),
            "placement_games_played": int(self.placement_games_played),
            "placement_games_required": int(self.placement_games_required),
            "placement_wins": int(self.placement_wins),
            "lp": int(self.lp),
            "in_promo": bool(self.in_promo),
            "promo_games_left": int(self.promo_games_left),
            "promo_wins": int(self.promo_wins),
            "promo_needed": int(self.promo_needed),
            "wins": int(self.wins),
            "losses": int(self.losses),
        }

    @staticmethod
    def from_dict(d: Dict) -> "Player":
        """Construct Player from a dict (as loaded from JSON)."""
        p = Player(
            id=int(d.get("id", 0)),
            name=str(d.get("name", f"Player_{d.get('id', 0)}")),
            rating=float(d.get("rating", _DEFAULT_RATING)),
        )
        p.win_streak = int(d.get("win_streak", 0))
        p.last_active = float(d.get("last_active", time.time()))
        p.history = list(d.get("history", []))
        p.tier = d.get("tier", rating_to_tier(p.rating))
        p.placed = bool(d.get("placed", False))
        p.placement_games_played = int(d.get("placement_games_played", 0))
        p.placement_games_required = int(d.get("placement_games_required", 0))
        p.placement_wins = int(d.get("placement_wins", 0))
        p.lp = int(d.get("lp", 0))
        p.in_promo = bool(d.get("in_promo", False))
        p.promo_games_left = int(d.get("promo_games_left", 0))
        p.promo_wins = int(d.get("promo_wins", 0))
        p.promo_needed = int(d.get("promo_needed", 0))
        p.wins = int(d.get("wins", 0))
        p.losses = int(d.get("losses", 0))
        return p


def load_players(path: str) -> List[Player]:
    """Load players from a JSON file. Returns empty list on missing file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        players: List[Player] = []
        for item in data:
            try:
                players.append(Player.from_dict(item))
            except Exception:
                # skip malformed entries but keep others
                continue
        return players
    except FileNotFoundError:
        return []
    except Exception as exc:
        # surface the error to caller
        raise RuntimeError(f"Failed to load players from {path}: {exc}") from exc


def save_players(path: str, players: List[Player]) -> None:
    """Save players list to JSON file atomically where possible."""
    try:
        payload = [p.to_dict() for p in players]
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        # atomic replace
        try:
            import os

            os.replace(tmp, path)
        except Exception:
            # fallback to non-atomic write
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        raise RuntimeError(f"Failed to save players to {path}: {exc}") from exc
