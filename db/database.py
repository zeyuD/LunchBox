"""
LunchBox — Database Manager
============================
Thin SQLite wrapper.  All SQL lives here; the rest of the app deals only with
model dataclasses.  Swap this file for a Postgres/ORM version without touching
any other module.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Generator, Optional

from db.schema import SCHEMA_SQL
from models.restaurant import Member, Restaurant, Visit

log = logging.getLogger(__name__)


class Database:
    """Manages a single SQLite connection and all CRUD operations."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ── Connection management ──────────────────────────────────────────────

    def connect(self) -> None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        log.debug("Connected to %s", self.db_path)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        assert self._conn, "Call connect() or use as context manager first."
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    # ── Schema ─────────────────────────────────────────────────────────────

    def create_all(self) -> None:
        """Create tables if they don't exist (idempotent)."""
        with self._cursor() as cur:
            cur.executescript(SCHEMA_SQL)
        log.info("Schema ready.")

    # ── Restaurants ────────────────────────────────────────────────────────

    def add_restaurant(self, r: Restaurant) -> int:
        sql = """
            INSERT INTO restaurants
                (name, address, distance_mile, food_type, avg_price,
                 avg_waiting_min, avg_eating_min, visited_times,
                 last_visited, internal_rating, is_active)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """
        with self._cursor() as cur:
            cur.execute(sql, (
                r.name, r.address, r.distance_mile, r.food_type, r.avg_price,
                r.avg_waiting_min, r.avg_eating_min, r.visited_times,
                r.last_visited.isoformat() if r.last_visited else None,
                r.internal_rating, int(r.is_active),
            ))
            return cur.lastrowid  # type: ignore[return-value]

    def update_restaurant(self, r: Restaurant) -> None:
        assert r.id is not None, "Restaurant must have an id to update."
        sql = """
            UPDATE restaurants SET
                name=?, address=?, distance_mile=?, food_type=?, avg_price=?,
                avg_waiting_min=?, avg_eating_min=?, visited_times=?,
                last_visited=?, internal_rating=?, is_active=?
            WHERE id=?
        """
        with self._cursor() as cur:
            cur.execute(sql, (
                r.name, r.address, r.distance_mile, r.food_type, r.avg_price,
                r.avg_waiting_min, r.avg_eating_min, r.visited_times,
                r.last_visited.isoformat() if r.last_visited else None,
                r.internal_rating, int(r.is_active), r.id,
            ))

    def get_restaurant(self, restaurant_id: int) -> Optional[Restaurant]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM restaurants WHERE id=?", (restaurant_id,))
            row = cur.fetchone()
        return _row_to_restaurant(row) if row else None

    def list_restaurants(
        self,
        active_only: bool = True,
        food_type: Optional[str] = None,
        max_price: Optional[float] = None,
        max_distance: Optional[float] = None,
    ) -> list[Restaurant]:
        conditions = []
        params: list = []

        if active_only:
            conditions.append("is_active = 1")
        if food_type:
            conditions.append("LOWER(food_type) = LOWER(?)")
            params.append(food_type)
        if max_price is not None:
            conditions.append("avg_price <= ?")
            params.append(max_price)
        if max_distance is not None:
            conditions.append("distance_mile <= ?")
            params.append(max_distance)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"SELECT * FROM restaurants {where} ORDER BY name"

        with self._cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_to_restaurant(r) for r in rows]

    def delete_restaurant(self, restaurant_id: int, soft: bool = True) -> None:
        with self._cursor() as cur:
            if soft:
                cur.execute(
                    "UPDATE restaurants SET is_active=0 WHERE id=?", (restaurant_id,)
                )
            else:
                cur.execute("DELETE FROM restaurants WHERE id=?", (restaurant_id,))

    # ── Members ────────────────────────────────────────────────────────────

    def add_member(self, m: Member) -> int:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO members (name, memid, active) VALUES (?,?,?)",
                (m.name, m.memid, int(m.active)),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def list_members(self, active_only: bool = True) -> list[Member]:
        where = "WHERE active=1" if active_only else ""
        with self._cursor() as cur:
            cur.execute(f"SELECT * FROM members {where} ORDER BY name")
            rows = cur.fetchall()
        return [Member(id=r["id"], name=r["name"], memid=r["memid"], active=bool(r["active"])) for r in rows]

    def get_member_by_name(self, name: str) -> Optional[Member]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM members WHERE LOWER(name)=LOWER(?)", (name,))
            row = cur.fetchone()
        if not row:
            return None
        return Member(id=row["id"], name=row["name"], memid=row["memid"], active=bool(row["active"]))

    # ── Visits ─────────────────────────────────────────────────────────────

    def record_visit(self, visit: Visit) -> int:
        """
        Persist a visit and update the restaurant's history fields atomically.
        Returns the new visit id.
        """
        with self._cursor() as cur:
            # 1. Insert visit row
            cur.execute(
                """INSERT INTO visits (restaurant_id, visit_date, rating_given, notes)
                   VALUES (?,?,?,?)""",
                (
                    visit.restaurant_id,
                    visit.visit_date.isoformat(),
                    visit.rating_given,
                    visit.notes,
                ),
            )
            visit_id = cur.lastrowid

            # 2. Link members
            for mid in visit.member_ids:
                cur.execute(
                    "INSERT OR IGNORE INTO visit_members (visit_id, member_id) VALUES (?,?)",
                    (visit_id, mid),
                )

            # 3. Update restaurant stats
            cur.execute(
                """UPDATE restaurants
                   SET visited_times = visited_times + 1,
                       last_visited  = ?,
                       internal_rating = CASE
                           WHEN ? IS NOT NULL
                           THEN ROUND((internal_rating + ?) / 2.0, 1)
                           ELSE internal_rating
                       END
                   WHERE id = ?""",
                (
                    visit.visit_date.isoformat(),
                    visit.rating_given,
                    visit.rating_given,
                    visit.restaurant_id,
                ),
            )
        log.info("Visit %d recorded for restaurant %d", visit_id, visit.restaurant_id)
        return visit_id  # type: ignore[return-value]

    def get_visits(self, restaurant_id: int) -> list[Visit]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM visits WHERE restaurant_id=? ORDER BY visit_date DESC",
                (restaurant_id,),
            )
            rows = cur.fetchall()
            visits = []
            for row in rows:
                cur.execute(
                    "SELECT member_id FROM visit_members WHERE visit_id=?", (row["id"],)
                )
                member_ids = [r["member_id"] for r in cur.fetchall()]
                visits.append(Visit(
                    id=row["id"],
                    restaurant_id=row["restaurant_id"],
                    visit_date=date.fromisoformat(row["visit_date"]),
                    rating_given=row["rating_given"],
                    notes=row["notes"],
                    member_ids=member_ids,
                ))
        return visits


# ── Helpers ────────────────────────────────────────────────────────────────────

def _row_to_restaurant(row: sqlite3.Row) -> Restaurant:
    last = row["last_visited"]
    return Restaurant(
        id=row["id"],
        name=row["name"],
        address=row["address"],
        distance_mile=row["distance_mile"],
        food_type=row["food_type"],
        avg_price=row["avg_price"],
        avg_waiting_min=row["avg_waiting_min"],
        avg_eating_min=row["avg_eating_min"],
        visited_times=row["visited_times"],
        last_visited=date.fromisoformat(last) if last else None,
        internal_rating=row["internal_rating"],
        is_active=bool(row["is_active"]),
    )
