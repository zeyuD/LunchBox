"""
LunchBox — Database Schema
==========================
All CREATE TABLE statements live here.
database.py calls `create_all()` on first run.
"""

SCHEMA_SQL = """
-- ── Restaurants ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS restaurants (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT    NOT NULL UNIQUE,
    address          TEXT    DEFAULT '',
    distance_mile      REAL    NOT NULL DEFAULT 0.0,
    food_type        TEXT    NOT NULL DEFAULT '',
    avg_price        REAL    NOT NULL DEFAULT 0.0,
    avg_waiting_min  REAL    NOT NULL DEFAULT 0.0,
    avg_eating_min   REAL    NOT NULL DEFAULT 30.0,
    visited_times    INTEGER NOT NULL DEFAULT 0,
    last_visited     TEXT    DEFAULT NULL,   -- ISO date string YYYY-MM-DD
    internal_rating  REAL    NOT NULL DEFAULT 5.0,
    is_active        INTEGER NOT NULL DEFAULT 1
);

-- ── Members ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS members (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT    NOT NULL UNIQUE,
    memid  TEXT    DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1
);

-- ── Visits ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS visits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
    visit_date    TEXT    NOT NULL,   -- ISO date YYYY-MM-DD
    rating_given  REAL    DEFAULT NULL,
    notes         TEXT    DEFAULT ''
);

-- ── Visit ↔ Member junction ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS visit_members (
    visit_id  INTEGER NOT NULL REFERENCES visits(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    PRIMARY KEY (visit_id, member_id)
);

-- ── Food type lookup (optional normalisation) ──────────────────────────────
CREATE TABLE IF NOT EXISTS food_types (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);
"""
