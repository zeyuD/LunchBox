"""
LunchBox — CLI Interface
========================
All user-facing I/O lives here.  Other modules stay pure.

Commands
--------
  decide   — Score & recommend restaurants for today's lunch
  add      — Add a new restaurant
  list     — List all restaurants
  visit    — Record a lunch visit
  members  — Add / list members
  rate     — Update a restaurant's internal rating
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from typing import Optional

import config
from core.filters import FilterConfig, apply_filters
from core.scorer import ScoringContext, WeightedScorer
from db.database import Database
from models.restaurant import Member, Restaurant, Visit

log = logging.getLogger(__name__)


# ── Entry point ────────────────────────────────────────────────────────────────

def run_cli(db: Database) -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(db, args)


# ── Sub-command: decide ────────────────────────────────────────────────────────

def cmd_decide(db: Database, args: argparse.Namespace) -> None:
    """Score and recommend restaurants."""

    # 1. Resolve available members
    available_members: list[Member] = []
    if args.members:
        for name in args.members:
            m = db.get_member_by_name(name)
            if m is None:
                print(f"  ⚠  Member '{name}' not found — skipping.")
            else:
                available_members.append(m)
    else:
        available_members = db.list_members()

    # 2. Build filter config
    cfg = FilterConfig(
        food_type         = args.food_type,
        max_price         = args.max_price,
        max_distance_mile   = args.max_distance,
        max_total_minutes = args.max_time,
        cooldown_days     = args.cooldown,
        min_rating        = args.min_rating,
    )

    # 3. Fetch & filter
    all_restaurants = db.list_restaurants(active_only=True)
    candidates = apply_filters(all_restaurants, cfg)

    if not candidates:
        print("\n  No restaurants match your filters.  Try relaxing constraints.\n")
        return

    # 4. Score & rank
    ctx = ScoringContext(available_members=available_members)
    scorer = WeightedScorer()
    ranked = scorer.rank(candidates, ctx)

    # 5. Display
    top_n = args.top or config.DEFAULT_TOP_N
    print(f"\n🍱  LunchBox Recommendations  ({date.today()})  "
          f"[{len(available_members)} member(s)]")
    print("─" * 58)
    for i, sr in enumerate(ranked[:top_n], 1):
        print(f"\n  #{i}")
        print(sr)
    print()

    if args.verbose:
        print("\n📊  Full breakdown:")
        print(f"  {'Restaurant':<25} " +
              "  ".join(f"{k[:7]:>7}" for k in config.SCORER_WEIGHTS))
        print("  " + "─" * 80)
        for sr in ranked[:top_n]:
            row = f"  {sr.restaurant.name:<25} "
            row += "  ".join(f"{sr.breakdown[k]:>7.3f}" for k in config.SCORER_WEIGHTS)
            print(row)
        print()


# ── Sub-command: add ───────────────────────────────────────────────────────────

def cmd_add(db: Database, args: argparse.Namespace) -> None:
    r = Restaurant(
        name            = args.name,
        address         = args.address or "",
        distance_mile     = args.distance,
        food_type       = args.food_type,
        avg_price       = args.price,
        avg_waiting_min = args.waiting,
        avg_eating_min  = args.eating,
        internal_rating = args.rating,
    )
    rid = db.add_restaurant(r)
    print(f"\n  ✅  Added '{r.name}' (id={rid})\n")


# ── Sub-command: list ──────────────────────────────────────────────────────────

def cmd_list(db: Database, args: argparse.Namespace) -> None:
    restaurants = db.list_restaurants(
        active_only  = not args.all,
        food_type    = args.food_type,
        max_price    = args.max_price,
        max_distance = args.max_distance,
    )
    if not restaurants:
        print("\n  No restaurants found.\n")
        return
    print(f"\n  {'ID':<4} {'Name':<25} {'Type':<12} {'$':>5} {'km':>5} "
          f"{'Wait':>5} {'Eat':>5} {'⭐':>5} {'Visits':>6}  Last visited")
    print("  " + "─" * 90)
    for r in restaurants:
        last = r.last_visited.isoformat() if r.last_visited else "—"
        print(
            f"  {r.id:<4} {r.name:<25} {r.food_type:<12} "
            f"{r.avg_price:>5.1f} {r.distance_mile:>5.1f} "
            f"{r.avg_waiting_min:>5.0f} {r.avg_eating_min:>5.0f} "
            f"{r.internal_rating:>5.1f} {r.visited_times:>6}  {last}"
        )
    print()


# ── Sub-command: visit ─────────────────────────────────────────────────────────

def cmd_visit(db: Database, args: argparse.Namespace) -> None:
    r = db.get_restaurant(args.id)
    if r is None:
        print(f"\n  ❌  Restaurant id={args.id} not found.\n")
        return

    member_ids: list[int] = []
    if args.members:
        for name in args.members:
            m = db.get_member_by_name(name)
            if m is None:
                print(f"  ⚠  Member '{name}' not found — skipping.")
            elif m.id is not None:
                member_ids.append(m.id)

    visit_date = date.fromisoformat(args.date) if args.date else date.today()

    v = Visit(
        restaurant_id = args.id,
        visit_date    = visit_date,
        rating_given  = args.rating,
        notes         = args.notes or "",
        member_ids    = member_ids,
    )
    vid = db.record_visit(v)
    print(f"\n  ✅  Visit recorded (id={vid}) for '{r.name}' on {visit_date}\n")


# ── Sub-command: rate ──────────────────────────────────────────────────────────

def cmd_rate(db: Database, args: argparse.Namespace) -> None:
    r = db.get_restaurant(args.id)
    if r is None:
        print(f"\n  ❌  Restaurant id={args.id} not found.\n")
        return
    r.internal_rating = max(0.0, min(10.0, args.rating))
    db.update_restaurant(r)
    print(f"\n  ✅  '{r.name}' internal rating updated to {r.internal_rating:.1f}\n")


# ── Sub-command: members ───────────────────────────────────────────────────────

def cmd_members(db: Database, args: argparse.Namespace) -> None:
    if args.add:
        m = Member(name=args.add, memid=args.memid or "")
        mid = db.add_member(m)
        print(f"\n  ✅  Member '{m.name}' added (id={mid})\n")
    else:
        members = db.list_members(active_only=not args.all)
        if not members:
            print("\n  No members found.\n")
            return
        print()
        for m in members:
            status = "✓" if m.active else "—"
            print(f"  [{status}] {m.id}: {m.name}  {m.memid}")
        print()


# ── Parser ─────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lunchbox",
        description="🍱  LunchBox — Let's decide where to eat.",
    )
    sub = parser.add_subparsers(title="commands")

    # decide
    p_decide = sub.add_parser("decide", help="Recommend restaurants for today")
    p_decide.add_argument("--members",     nargs="+", metavar="NAME",
                          help="Names of members joining today")
    p_decide.add_argument("--food-type",   metavar="TYPE",
                          help="Filter by food type (e.g. noodles)")
    p_decide.add_argument("--max-price",   type=float, metavar="$")
    p_decide.add_argument("--max-distance",type=float, metavar="KM")
    p_decide.add_argument("--max-time",    type=float, metavar="MIN",
                          help="Max total time (wait + eat) in minutes")
    p_decide.add_argument("--cooldown",    type=int, metavar="DAYS",
                          help="Skip restaurants visited within N days")
    p_decide.add_argument("--min-rating",  type=float, metavar="STARS")
    p_decide.add_argument("--top",         type=int, metavar="N",
                          help=f"Show top N results (default {config.DEFAULT_TOP_N})")
    p_decide.add_argument("--verbose", "-v", action="store_true",
                          help="Show per-factor score breakdown")
    p_decide.set_defaults(func=cmd_decide)

    # add
    p_add = sub.add_parser("add", help="Add a new restaurant")
    p_add.add_argument("name",               help="Restaurant name")
    p_add.add_argument("--food-type",  "-f", required=True, metavar="TYPE")
    p_add.add_argument("--distance",   "-d", required=True, type=float, metavar="KM")
    p_add.add_argument("--price",      "-p", required=True, type=float, metavar="$")
    p_add.add_argument("--waiting",    "-w", default=10.0,  type=float, metavar="MIN")
    p_add.add_argument("--eating",     "-e", default=30.0,  type=float, metavar="MIN")
    p_add.add_argument("--rating",     "-r", default=5.0,   type=float, metavar="1-10")
    p_add.add_argument("--address",    "-a", default="")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = sub.add_parser("list", help="List restaurants")
    p_list.add_argument("--food-type",    metavar="TYPE")
    p_list.add_argument("--max-price",    type=float, metavar="$")
    p_list.add_argument("--max-distance", type=float, metavar="KM")
    p_list.add_argument("--all",          action="store_true",
                        help="Include inactive (soft-deleted) restaurants")
    p_list.set_defaults(func=cmd_list)

    # visit
    p_visit = sub.add_parser("visit", help="Record a lunch visit")
    p_visit.add_argument("id",            type=int,   help="Restaurant id")
    p_visit.add_argument("--members",     nargs="+",  metavar="NAME")
    p_visit.add_argument("--rating",      type=float, metavar="1-10",
                         help="Post-visit rating (updates restaurant average)")
    p_visit.add_argument("--date",        metavar="YYYY-MM-DD",
                         help="Visit date (default: today)")
    p_visit.add_argument("--notes",       metavar="TEXT")
    p_visit.set_defaults(func=cmd_visit)

    # rate
    p_rate = sub.add_parser("rate", help="Update a restaurant's internal rating")
    p_rate.add_argument("id",     type=int,   help="Restaurant id")
    p_rate.add_argument("rating", type=float, help="New rating (1.0 – 10.0)")
    p_rate.set_defaults(func=cmd_rate)

    # members
    p_mem = sub.add_parser("members", help="Manage team members")
    p_mem.add_argument("--add",   metavar="NAME",  help="Add a new member")
    p_mem.add_argument("--memid", metavar="Memid", help="Memid for new member")
    p_mem.add_argument("--all",   action="store_true",
                       help="Include inactive members")
    p_mem.set_defaults(func=cmd_members)

    return parser
