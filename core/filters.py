"""
LunchBox — Filters
==================
Hard constraints that eliminate restaurants before scoring.
Decoupled from the scorer so each can evolve independently.

All filter functions take a list[Restaurant] and return a filtered list.
Chain them with `apply_filters()`.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional

from models.restaurant import Restaurant


# ── Individual filter functions ────────────────────────────────────────────────

def by_food_type(restaurants: list[Restaurant], food_type: str) -> list[Restaurant]:
    """Keep only restaurants whose food_type matches (case-insensitive)."""
    ft = food_type.strip().lower()
    return [r for r in restaurants if r.food_type.lower() == ft]


def by_max_price(restaurants: list[Restaurant], max_price: float) -> list[Restaurant]:
    return [r for r in restaurants if r.avg_price <= max_price]


def by_max_distance(restaurants: list[Restaurant], max_km: float) -> list[Restaurant]:
    return [r for r in restaurants if r.distance_mile <= max_km]


def by_max_total_time(
    restaurants: list[Restaurant], max_minutes: float
) -> list[Restaurant]:
    """Filter by total time = waiting + eating."""
    return [r for r in restaurants if (r.avg_waiting_min + r.avg_eating_min) <= max_minutes]


def exclude_recently_visited(
    restaurants: list[Restaurant], cooldown_days: int = 7
) -> list[Restaurant]:
    """
    Exclude restaurants visited within the last `cooldown_days` days.
    Restaurants never visited pass through.
    """
    cutoff = date.today() - timedelta(days=cooldown_days)
    return [
        r for r in restaurants
        if r.last_visited is None or r.last_visited < cutoff
    ]


def by_min_rating(restaurants: list[Restaurant], min_rating: float) -> list[Restaurant]:
    return [r for r in restaurants if r.internal_rating >= min_rating]


# ── Aggregated filter pipeline ─────────────────────────────────────────────────

class FilterConfig:
    """
    Bundles all optional filter parameters.
    Pass an instance to `apply_filters()`.
    """

    def __init__(
        self,
        food_type: Optional[str] = None,
        max_price: Optional[float] = None,
        max_distance_mile: Optional[float] = None,
        max_total_minutes: Optional[float] = None,
        cooldown_days: Optional[int] = None,   # None = no cooldown filter
        min_rating: Optional[float] = None,
    ) -> None:
        self.food_type         = food_type
        self.max_price         = max_price
        self.max_distance_mile   = max_distance_mile
        self.max_total_minutes = max_total_minutes
        self.cooldown_days     = cooldown_days
        self.min_rating        = min_rating

    def __str__(self) -> str:
        active = {k: v for k, v in self.__dict__.items() if v is not None}
        return f"FilterConfig({active})"


def apply_filters(
    restaurants: list[Restaurant],
    cfg: FilterConfig,
) -> list[Restaurant]:
    """
    Apply all configured filters sequentially and return the survivors.
    Order matters: cheap checks first to prune early.
    """
    result = list(restaurants)

    if cfg.food_type:
        result = by_food_type(result, cfg.food_type)
    if cfg.max_price is not None:
        result = by_max_price(result, cfg.max_price)
    if cfg.max_distance_mile is not None:
        result = by_max_distance(result, cfg.max_distance_mile)
    if cfg.max_total_minutes is not None:
        result = by_max_total_time(result, cfg.max_total_minutes)
    if cfg.min_rating is not None:
        result = by_min_rating(result, cfg.min_rating)
    if cfg.cooldown_days is not None:
        result = exclude_recently_visited(result, cfg.cooldown_days)

    return result
