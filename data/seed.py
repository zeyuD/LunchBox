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
        name="Pho Saigon",
        food_type="noodles",
        distance_mile=0.4,
        avg_price=12.0,
        avg_waiting_min=5,
        avg_eating_min=25,
        internal_rating=8.5,
        address="12 Main St",
    ),
    Restaurant(
        name="Burger Barn",
        food_type="fast food",
        distance_mile=0.2,
        avg_price=10.0,
        avg_waiting_min=8,
        avg_eating_min=20,
        internal_rating=6.5,
        address="4 Oak Ave",
    ),
    Restaurant(
        name="Sakura Sushi",
        food_type="sushi",
        distance_mile=1.2,
        avg_price=22.0,
        avg_waiting_min=15,
        avg_eating_min=45,
        internal_rating=9.0,
        address="88 Cherry Ln",
    ),
    Restaurant(
        name="Golden Wok",
        food_type="chinese",
        distance_mile=0.7,
        avg_price=13.0,
        avg_waiting_min=10,
        avg_eating_min=30,
        internal_rating=7.5,
        address="22 Elm Rd",
    ),
    Restaurant(
        name="Pizza Palace",
        food_type="pizza",
        distance_mile=0.9,
        avg_price=14.0,
        avg_waiting_min=12,
        avg_eating_min=35,
        internal_rating=7.0,
        address="7 Napoli Blvd",
    ),
    Restaurant(
        name="Taco Loco",
        food_type="mexican",
        distance_mile=1.5,
        avg_price=11.0,
        avg_waiting_min=7,
        avg_eating_min=20,
        internal_rating=7.8,
        address="33 Cactus Way",
    ),
    Restaurant(
        name="The Sandwich Lab",
        food_type="sandwiches",
        distance_mile=0.3,
        avg_price=9.0,
        avg_waiting_min=5,
        avg_eating_min=20,
        internal_rating=8.0,
        address="5 Deli Court",
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
        (ids.get("Pho Saigon"),       date.today() - timedelta(days=10), [1, 2], 8.0),
        (ids.get("Burger Barn"),       date.today() - timedelta(days=3),  [1, 3], 6.0),
        (ids.get("Sakura Sushi"),      date.today() - timedelta(days=20), [1, 2, 3, 4], 9.5),
        (ids.get("The Sandwich Lab"),  date.today() - timedelta(days=5),  [2, 4], 8.0),
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
