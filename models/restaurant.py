"""
LunchBox — Data Models
======================
Pure dataclasses with no DB or I/O dependencies.
Import these anywhere without side-effects.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Restaurant:
    """Represents one restaurant entry in the database."""

    # Identity
    id:             Optional[int]   = None
    name:           str             = ""
    address:        str             = ""

    # Logistics
    distance_mile:  float           = 0.0   # from office / base location
    food_type:      str             = ""    # e.g. "fast food", "noodles", "sushi"
    avg_price:      float           = 0.0   # average spend per person ($)
    avg_waiting_min:float           = 0.0   # estimated wait before seated / served
    avg_eating_min: float           = 30.0  # estimated time to finish the meal

    # History
    visited_times:  int             = 0
    last_visited:   Optional[date]  = None  # None = never visited

    # Rating
    internal_rating:float           = 5.0   # 1.0 – 10.0, set by the group

    # Meta
    is_active:      bool            = True  # soft-delete flag

    def __str__(self) -> str:
        last = self.last_visited.isoformat() if self.last_visited else "never"
        return (
            f"[{self.id}] {self.name} | {self.food_type} | "
            f"${self.avg_price:.1f} | {self.distance_mile:.1f} km | "
            f"⭐ {self.internal_rating:.1f} | visited {self.visited_times}x (last: {last})"
        )


@dataclass
class Member:
    """Represents a team member who may join lunch."""

    id:     Optional[int] = None
    name:   str           = ""
    memid:  str           = ""
    active: bool          = True

    def __str__(self) -> str:
        return f"[{self.id}] {self.name}"


@dataclass
class Visit:
    """One recorded lunch visit — links a restaurant to attendees."""

    id:            Optional[int]  = None
    restaurant_id: int            = 0
    visit_date:    date           = field(default_factory=date.today)
    rating_given:  Optional[float]= None   # post-visit rating override (1–10)
    notes:         str            = ""
    member_ids:    list[int]      = field(default_factory=list)  # not stored in visits table
