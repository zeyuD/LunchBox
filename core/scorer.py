"""
LunchBox — Scorer
=================
Converts a list of Restaurant objects into a ranked list of ScoredRestaurant.

Design contract (for future ML replacement):
    Any scorer must implement the `BaseScorer` interface:
        rank(restaurants, context) -> list[ScoredRestaurant]

The default `WeightedScorer` is a transparent, config-driven linear model.
Replace it with `MLScorer` or any other subclass in main.py without touching
filters, CLI, or database code.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import config
from models.restaurant import Member, Restaurant

log = logging.getLogger(__name__)


# ── Scored result ──────────────────────────────────────────────────────────────

@dataclass
class ScoredRestaurant:
    restaurant: Restaurant
    score: float                             # final composite score [0, 1]
    breakdown: dict[str, float] = field(default_factory=dict)  # per-factor scores

    def __str__(self) -> str:
        bar = "█" * int(self.score * 20) + "░" * (20 - int(self.score * 20))
        return (
            f"  {self.restaurant.name:<25} [{bar}] {self.score:.3f}\n"
            f"    ↳ {self.restaurant.food_type} | "
            f"${self.restaurant.avg_price:.0f} | "
            f"{self.restaurant.distance_mile:.1f} km | "
            f"wait {self.restaurant.avg_waiting_min:.0f} min | "
            f"⭐ {self.restaurant.internal_rating:.1f}"
        )


# ── Scoring context (runtime inputs) ──────────────────────────────────────────

@dataclass
class ScoringContext:
    """
    Runtime state passed to the scorer.
    Extend this (e.g. add weather, day-of-week) without changing the scorer API.
    """
    available_members: list[Member] = field(default_factory=list)
    today: date = field(default_factory=date.today)


# ── Base interface ─────────────────────────────────────────────────────────────

class BaseScorer(ABC):
    """Interface all scorers must implement."""

    @abstractmethod
    def rank(
        self,
        restaurants: list[Restaurant],
        context: ScoringContext,
    ) -> list[ScoredRestaurant]:
        ...


# ── Default: Weighted linear scorer ───────────────────────────────────────────

class WeightedScorer(BaseScorer):
    """
    Scores each restaurant by normalising each factor to [0, 1] and computing
    a weighted sum.  Weights and normalisation ranges come from config.py.

    Factors and their polarity:
        distance        → lower  is better
        price           → lower  is better
        waiting_time    → lower  is better
        eating_time     → lower  is better
        internal_rating → higher is better
        recency_penalty → recently visited → lower score
    """

    def __init__(
        self,
        weights: Optional[dict[str, float]] = None,
        norm: Optional[dict[str, float]] = None,
    ) -> None:
        self.weights = weights or config.SCORER_WEIGHTS
        self.norm    = norm    or config.NORM
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            log.warning("Scorer weights sum to %.4f (expected 1.0) — normalising.", total)
            self.weights = {k: v / total for k, v in self.weights.items()}

    # ── Public API ─────────────────────────────────────────────────────────

    def rank(
        self,
        restaurants: list[Restaurant],
        context: ScoringContext,
    ) -> list[ScoredRestaurant]:
        if not restaurants:
            return []
        scored = [self._score_one(r, context) for r in restaurants]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored

    # ── Internal helpers ───────────────────────────────────────────────────

    def _score_one(self, r: Restaurant, ctx: ScoringContext) -> ScoredRestaurant:
        w = self.weights
        n = self.norm

        # Each sub-score in [0, 1]; higher = better
        s_distance = self._invert(r.distance_mile,      n["distance_max"])
        s_price    = self._invert(r.avg_price,         n["price_max"])
        s_waiting  = self._invert(r.avg_waiting_min,   n["waiting_time_max"])
        s_eating   = self._invert(r.avg_eating_min,    n["eating_time_max"])
        s_rating   = r.internal_rating / 10.0

        # Recency: 0 if visited today, 1 if not visited in recency_days_max+
        if r.last_visited is None:
            s_recency = 1.0
        else:
            days_ago = (ctx.today - r.last_visited).days
            s_recency = min(days_ago / n["recency_days_max"], 1.0)

        breakdown = {
            "distance":        s_distance,
            "price":           s_price,
            "waiting_time":    s_waiting,
            "eating_time":     s_eating,
            "internal_rating": s_rating,
            "recency_penalty": s_recency,
        }

        final = sum(breakdown[k] * w[k] for k in breakdown)

        return ScoredRestaurant(restaurant=r, score=round(final, 4), breakdown=breakdown)

    @staticmethod
    def _invert(value: float, max_value: float) -> float:
        """Map [0, max_value] → [1, 0] (lower raw value → higher score)."""
        if max_value <= 0:
            return 1.0
        return max(0.0, 1.0 - value / max_value)
