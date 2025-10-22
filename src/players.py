# players.py — model with LP, placement and promo
from dataclasses import dataclass, field
from typing import List, Dict
import time
import json

from src.ranks import rating_to_tier, TIERS, DIVISIONS

@dataclass
class Player:
    id: int
    name: str
    rating: float = 1500.0
    win_streak: int = 0
    last_active: float = field(default_factory=lambda: time.time())
    history: List[Dict] = field(default_factory=list)
    tier: Dict = field(default_factory=lambda: rating_to_tier(1500.0))

    # Placement / initial calibration
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

    def record_match(self, opponent_id: int, result: float, delta: float, lp_change: int = 0, placement: bool = False):
        """
        Record a match for player.
        result: 1.0 win, 0.5 draw, 0.0 loss
        delta: rating change (float)
        lp_change: integer change in LP (positive for wins etc.)
        placement: whether this match counts toward placement
        """
        self.last_active = time.time()
        if result == 1.0:
            self.win_streak += 1
        else:
            self.win_streak = 0

        # rating change
        self.rating += delta

        # placement logic
        if placement and not self.placed:
            self.placement_games_played += 1
            if result == 1.0:
                self.placement_wins += 1
            if self.placement_games_played >= self.placement_games_required:
                self.placed = True
                # simplistic placement reward: wins > half -> bump rating & LP
                if self.placement_wins > (self.placement_games_required // 2):
                    self.lp += 20 * self.placement_wins
                    self.rating += 15.0
                else:
                    self.lp += max(0, 5 * self.placement_wins)

        # LP / promo
        if lp_change != 0:
            self.apply_lp(lp_change)

        # recalc tier
        self.tier = rating_to_tier(self.rating)

        # append history
        self.history.append({
            "time": self.last_active,
            "opponent_id": opponent_id,
            "result": result,
            "delta": delta,
            "rating": self.rating,
            "lp": self.lp,
            "tier": self.tier,
        })

    def apply_lp(self, amount: int):
        # if in promo, treat differently
        if self.in_promo:
            if amount > 0:
                self.promo_wins += 1
            self.promo_games_left = max(0, self.promo_games_left - 1)
            if self.promo_games_left == 0:
                self.resolve_promo()
            return

        self.lp += amount
        if self.lp < 0:
            self.lp = 0
        if self.lp >= 100:
            # enter promo series (best of 3 default)
            self.enter_promo(best_of=3)

    def enter_promo(self, best_of: int = 3):
        self.in_promo = True
        self.promo_games_left = best_of
        self.promo_wins = 0
        self.promo_needed = (best_of // 2) + 1

    def resolve_promo(self):
        success = self.promo_wins >= self.promo_needed
        self.in_promo = False
        self.promo_games_left = 0
        self.promo_wins = 0
        self.promo_needed = 0
        if success:
            self.promote_to_next_division()
            self.lp = 0
        else:
            self.lp = max(0, self.lp - 50)
            self.rating = max(100.0, self.rating - 10.0)
        self.tier = rating_to_tier(self.rating)

    def promote_to_next_division(self):
        current_tier = self.tier.get("tier")
        current_div = self.tier.get("division")
        idx = next((i for i, t in enumerate(TIERS) if t[0] == current_tier), 0)
        try:
            div_idx = DIVISIONS.index(current_div)
        except ValueError:
            div_idx = 3
        if div_idx > 0:
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
            if idx + 1 < len(TIERS):
                new_tier = TIERS[idx + 1][0]
                new_div = DIVISIONS[-1]
                tier_min = TIERS[idx + 1][1]
                new_rating = tier_min + 10
            else:
                new_tier = current_tier
                new_div = current_div
                new_rating = self.rating + 30
        self.rating = new_rating
        self.tier = {"tier": new_tier, "division": new_div, "color": self.tier.get("color")}

    def apply_decay(self, decay_amount: float):
        self.rating = max(100.0, self.rating - decay_amount)
        self.tier = rating_to_tier(self.rating)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "rating": self.rating,
            "win_streak": self.win_streak,
            "last_active": self.last_active,
            "history": self.history,
            "tier": self.tier,
            "placed": self.placed,
            "placement_games_played": self.placement_games_played,
            "placement_games_required": self.placement_games_required,
            "placement_wins": self.placement_wins,
            "lp": self.lp,
            "in_promo": self.in_promo,
        }

    @staticmethod
    def from_dict(d: Dict) -> "Player":
        p = Player(id=d["id"], name=d.get("name", f"player_{d['id']}"), rating=d.get("rating", 1500.0))
        p.win_streak = d.get("win_streak", 0)
        p.last_active = d.get("last_active", time.time())
        p.history = d.get("history", [])
        p.tier = d.get("tier", rating_to_tier(p.rating))
        p.placed = d.get("placed", False)
        p.placement_games_played = d.get("placement_games_played", 0)
        p.placement_games_required = d.get("placement_games_required", 0)
        p.placement_wins = d.get("placement_wins", 0)
        p.lp = d.get("lp", 0)
        p.in_promo = d.get("in_promo", False)
        return p

def load_players(path: str) -> List[Player]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Player.from_dict(d) for d in data]
    except FileNotFoundError:
        return []

def save_players(path: str, players: List[Player]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in players], f, indent=2)
