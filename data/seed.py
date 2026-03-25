"""
LunchBox — Seed Data
====================
Populates the database with sample restaurants and members for testing.
Run directly:  python -m data.seed
"""

from datetime import date, timedelta

from db.database import Database
from models.restaurant import Member, Restaurant, Visit
import config


SAMPLE_RESTAURANTS = [
    Restaurant(
        name="Zaap Kitchen",
        food_type="thai",
        distance_mile=2.2,
        avg_price=15.0,
        avg_waiting_min=10,
        avg_eating_min=25,
        internal_rating=9.0,
        address="6107 Greenville Ave, Dallas, TX 75206",
    ),
    Restaurant(
        name="Chick-fil-A",
        food_type="fast food",
        distance_mile=0.1,
        avg_price=10.0,
        avg_waiting_min=8,
        avg_eating_min=20,
        internal_rating=8.5,
        address="3140 Dyer St, Dallas, TX 75205",
    ),
    Restaurant(
        name="Raising Cane's",
        food_type="fast food",
        distance_mile=1.4,
        avg_price=10.0,
        avg_waiting_min=8,
        avg_eating_min=20,
        internal_rating=9.0,
        address="5030 Greenville Ave, Dallas, TX 75206",
    ),
    Restaurant(
        name="Panda Express",
        food_type="chinese",
        distance_mile=1.6,
        avg_price=13.0,
        avg_waiting_min=10,
        avg_eating_min=20,
        internal_rating=7.0,
        address="5500 Greenville Ave Suite 200, Dallas, TX 75206",
    ),
    Restaurant(
        name="Hometown Cafe",
        food_type="chinese",
        distance_mile=9.5,
        avg_price=13.0,
        avg_waiting_min=1,
        avg_eating_min=20,
        internal_rating=8.5,
        address="400 N Greenville Ave Ste 17, Richardson, TX 75081",
    ),
    Restaurant(
        name="Shake Shack",
        food_type="fast food",
        distance_mile=1.6,
        avg_price=15.0,
        avg_waiting_min=10,
        avg_eating_min=20,
        internal_rating=7.0,
        address="5500 Greenville Ave Ste. 505, Dallas, TX 75206",
    ),
    Restaurant(
        name="Rusty Taco",
        food_type="taco",
        distance_mile=1.2,
        avg_price=10.0,
        avg_waiting_min=10,
        avg_eating_min=20,
        internal_rating=8.0,
        address="4802 Greenville Ave, Dallas, TX 75206",
    ),
]

SAMPLE_MEMBERS = [
    Member(name="Zeyu",        memid="labmem001"),
    Member(name="Jingwei",     memid="labmem002"),
    Member(name="Wen",         memid="labmem003"),
    Member(name="Sihang",      memid="labmem004"),
]


def seed(db: Database) -> None:
    print("Seeding members...")
    for m in SAMPLE_MEMBERS:
        try:
            mid = db.add_member(m)
            print(f"  + {m.name} (id={mid})")
        except Exception as e:
            print(f"  ! {m.name}: {e}")

    print("\nSeeding restaurants...")
    ids: dict[str, int] = {}
    for r in SAMPLE_RESTAURANTS:
        try:
            rid = db.add_restaurant(r)
            ids[r.name] = rid
            print(f"  + {r.name} (id={rid})")
        except Exception as e:
            print(f"  ! {r.name}: {e}")

    print("\nSeeding visit history...")
    # Simulate some past visits
    sample_visits = [
        (ids.get("Zaap Kitchen"),        date.today() - timedelta(days=2),  [1, 2, 3],  8.0),
        (ids.get("Raising Cane's"),      date.today() - timedelta(days=3),  [1, 2],     6.0),
        (ids.get("Hometown Cafe"),       date.today() - timedelta(days=0),  [1, 2, 3],  9.5),
    ]
    for rid, vdate, mids, rating in sample_visits:
        if rid is None:
            continue
        try:
            v = Visit(restaurant_id=rid, visit_date=vdate,
                      rating_given=rating, member_ids=mids)
            vid = db.record_visit(v)
            print(f"  + visit id={vid} → restaurant {rid} on {vdate}")
        except Exception as e:
            print(f"  ! visit for restaurant {rid}: {e}")

    print("\n✅  Seed complete.\n")


if __name__ == "__main__":
    with Database(config.DB_PATH) as db:
        db.create_all()
        seed(db)
