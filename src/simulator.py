"""
Batch simulator for Player vs Player matches.
Depends on src/players.py (Player) and src/elo_system.py.
"""
import random
import time
from typing import List, Optional
from src.players import Player, load_players, save_players
from src.elo_system import expected_score, two_player_updates

class Simulator:
    def __init__(self, players: List[Player], k: float = 32.0,
                 arcade_mode: bool = False, streak_bonus_pct: float = 0.0,
                 decay_per_day: float = 0.0):
        self.players = players
        self.k = k
        self.arcade_mode = arcade_mode
        self.streak_bonus_pct = streak_bonus_pct  # e.g. 0.1 -> 10%
        self.decay_per_day = decay_per_day

    def pick_matchmaking_pair(self) -> Optional[tuple]:
        """Pick two distinct players. Default random; can be replaced by rating-proximity logic."""
        if len(self.players) < 2:
            return None
        a, b = random.sample(self.players, 2)
        return a, b

    def simulate_match(self, a: Player, b: Player) -> dict:
        """Simulate single match between players a and b. Returns match record dict."""
        pa = expected_score(a.rating, b.rating)
        # sample outcome: probability pa for a to win, 1-pa for b
        r = random.random()
        if r < pa:
            result_a = 1.0
            result_b = 0.0
        else:
            result_a = 0.0
            result_b = 1.0

        # compute streak bonuses if arcade mode
        sb_a = self.streak_bonus_pct * a.win_streak if self.arcade_mode else 0.0
        sb_b = self.streak_bonus_pct * b.win_streak if self.arcade_mode else 0.0

        delta_a, delta_b = two_player_updates(a.rating, b.rating, result_a,
                                              k=self.k, streak_bonus_a=sb_a,
                                              streak_bonus_b=sb_b)

        # record matches
        a.record_match(opponent_id=b.id, result=result_a, delta=delta_a)
        b.record_match(opponent_id=a.id, result=result_b, delta=delta_b)

        return {
            "time": time.time(),
            "player_a": a.id,
            "player_b": b.id,
            "result_a": result_a,
            "delta_a": delta_a,
            "rating_a": a.rating,
            "rating_b": b.rating,
        }

    def run_batch(self, matches: int = 1000, seed: Optional[int] = None) -> List[dict]:
        """Run a number of random matches and return list of match records."""
        if seed is not None:
            random.seed(seed)
        records = []
        for _ in range(matches):
            pair = self.pick_matchmaking_pair()
            if pair is None:
                break
            a, b = pair
            rec = self.simulate_match(a, b)
            records.append(rec)
        return records

    def apply_decay(self, inactive_seconds: float):
        """Apply rating decay to players who were inactive longer than inactive_seconds."""
        now = time.time()
        for p in self.players:
            inactive = now - p.last_active
            if inactive > inactive_seconds and self.decay_per_day > 0:
                days = inactive / (24 * 3600)
                decay_amount = self.decay_per_day * days
                p.apply_decay(decay_amount)

    @staticmethod
    def load_from_file(path: str) -> List[Player]:
        return load_players(path)

    @staticmethod
    def save_to_file(path: str, players: List[Player]) -> None:
        save_players(path, players)
