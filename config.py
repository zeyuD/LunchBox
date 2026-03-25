"""
LunchBox Configuration
======================
Central place for all tunable constants.
Swap scorer weights here — or override via env — without touching business logic.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "data" / "lunchbox.db"

# ── Scorer weights (must sum to 1.0) ──────────────────────────────────────────
# These are the default weights for the rule-based scorer (core/scorer.py).
# A future ML scorer can ignore these entirely.
SCORER_WEIGHTS = {
    "distance":       0.15,   # km — closer is better
    "price":          0.15,   # $ — cheaper is better
    "waiting_time":   0.20,   # minutes — shorter is better
    "eating_time":    0.10,   # minutes — shorter is better (for tight lunches)
    "internal_rating":0.25,   # 1–10 — higher is better
    "recency_penalty":0.15,   # days since last visit — visited recently → lower score
}

# ── Normalization reference ranges ────────────────────────────────────────────
# Used to scale raw values to [0, 1].  Adjust to match your real-world context.
NORM = {
    "distance_max":       5.0,    # km — anything ≥ this scores 0
    "price_max":         30.0,    # $ per person
    "waiting_time_max":  30.0,    # minutes
    "eating_time_max":   60.0,    # minutes
    "recency_days_max":  30,      # days — not visited in 30+ days → no penalty
}

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_TOP_N       = 3      # how many recommendations to show
MIN_RATING_FILTER   = 0.0    # skip restaurants below this internal rating
