# ranks.py
# League-like tier system: Iron -> Challenger with divisions IV -> I (IV is lowest)
from typing import Dict, Tuple

# Define tiers with minimum rating thresholds (example thresholds; you can tweak)
TIERS = [
    ("Iron", 1000),
    ("Bronze", 1100),
    ("Silver", 1200),
    ("Gold", 1300),
    ("Platinum", 1400),
    ("Diamond", 1550),
    ("Master", 1700),
    ("Grandmaster", 1850),
    ("Challenger", 2000),
]

DIVISIONS = ["IV", "III", "II", "I"]  # 4 divisions per tier (except top tiers could be single-division)

TIER_COLORS: Dict[str, str] = {
    "Iron": "#6b6b6b",
    "Bronze": "#cd7f32",
    "Silver": "#c0c0c0",
    "Gold": "#ffd700",
    "Platinum": "#2ee8c7",
    "Diamond": "#4cc9ff",
    "Master": "#a64dff",
    "Grandmaster": "#ff6b6b",
    "Challenger": "#ffb86b",
}

def rating_to_tier(rating: float) -> Dict[str, str]:
    """
    Map numeric rating to a tier+division representation.
    Returns dict: {"tier": "...", "division": "...", "color": "..."}
    """
    # If rating below first threshold -> Iron IV
    tier_name, tier_min = TIERS[0]
    for i, (name, min_rating) in enumerate(TIERS):
        tier_name, tier_min = name, min_rating
        # proceed until next tier would be higher than rating
        if i + 1 < len(TIERS):
            next_min = TIERS[i + 1][1]
            if rating < next_min:
                break
        else:
            # last tier (Challenger), assign it
            break

    # Determine division: divide range [tier_min, next_tier_min) into 4 equal parts
    # For top tier, just assign division I
    idx = next((i for i, t in enumerate(TIERS) if t[0] == tier_name), 0)
    if idx + 1 < len(TIERS):
        tier_start = TIERS[idx][1]
        tier_end = TIERS[idx + 1][1]
        span = tier_end - tier_start
        if span <= 0:
            division = "I"
        else:
            rel = max(0.0, min(1.0, (rating - tier_start) / span))
            # higher rating -> better division (I is best). Map rel [0..1) to divisions IV..I
            division_index = min(3, int(rel * 4))
            # convert so high rel -> smaller index for divisions list reversed
            division = DIVISIONS[max(0, 3 - division_index)]
    else:
        division = "I"

    return {"tier": tier_name, "division": division, "color": TIER_COLORS.get(tier_name, "#cccccc")}
