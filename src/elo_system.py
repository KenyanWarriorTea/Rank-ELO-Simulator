"""ELO system: expected score and rating delta calculation.
"""
from typing import Tuple

def expected_score(rating_a: float, rating_b: float) -> float:
    """Return expected score for player A against player B."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

def elo_delta(rating_a: float, rating_b: float, result: float, k: float = 32.0,
              streak_bonus: float = 0.0) -> float:
    """
    Compute rating change (delta) for player A.
    result: 1.0 win, 0.5 draw, 0.0 loss
    streak_bonus: additional multiplier (e.g. 0.1 means +10% for winning streak)
    """
    exp = expected_score(rating_a, rating_b)
    base_delta = k * (result - exp)
    # Apply small bonus on positive deltas if streak bonus specified
    if base_delta > 0 and streak_bonus:
        base_delta *= (1.0 + streak_bonus)
    return base_delta

def two_player_updates(rating_a: float, rating_b: float, result_a: float,
                       k: float = 32.0, streak_bonus_a: float = 0.0,
                       streak_bonus_b: float = 0.0) -> Tuple[float, float]:
    """
    Compute deltas for both players given result for A.
    Returns (delta_a, delta_b) where delta_b = -delta_a (conservation).
    """
    da = elo_delta(rating_a, rating_b, result_a, k, streak_bonus_a)
    db = -da
    # If you wanted asymmetric K or bonuses for loser, adjust here.
    return da, db
