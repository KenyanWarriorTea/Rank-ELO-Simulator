from dataclasses import dataclass, field
from typing import List, Dict
import time
import json

@dataclass
class Player:
    id: int
    name: str
    rating: float = 1500.0
    win_streak: int = 0
    last_active: float = field(default_factory=lambda: time.time())
    history: List[Dict] = field(default_factory=list)

    def record_match(self, opponent_id: int, result: float, delta: float) -> None:
        """Record a match result for this player.

        result: 1.0 = win, 0.5 = draw, 0.0 = loss
        delta: change in rating (can be negative)
        """
        self.last_active = time.time()
        if result == 1.0:
            self.win_streak += 1
        else:
            self.win_streak = 0
        self.rating += delta
        self.history.append({
            "time": self.last_active,
            "opponent_id": opponent_id,
            "result": result,
            "delta": delta,
            "rating": self.rating,
        })

    def apply_decay(self, decay_amount: float) -> None:
        """Apply rating decay due to inactivity."""
        self.rating = max(100.0, self.rating - decay_amount)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "rating": self.rating,
            "win_streak": self.win_streak,
            "last_active": self.last_active,
            "history": self.history,
        }

    @staticmethod
    def from_dict(d: Dict) -> "Player":
        p = Player(id=d["id"], name=d.get("name", f"player_{d['id']}"), rating=d.get("rating", 1500.0))
        p.win_streak = d.get("win_streak", 0)
        p.last_active = d.get("last_active", time.time())
        p.history = d.get("history", [])
        return p

# Helper functions for loading/saving player lists

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