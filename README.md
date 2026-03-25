# LunchBox

A modular CLI tool for deciding where to go for lunch.

## Project Structure

```
LunchBox/
├── main.py              # Entry point — wires DB + CLI
├── config.py            # Scorer weights, paths, normalization ranges
├── requirements.txt
│
├── db/
│   ├── schema.py        # All CREATE TABLE SQL
│   └── database.py      # Database manager (CRUD, no business logic)
│
├── models/
│   └── restaurant.py    # Restaurant, Member, Visit dataclasses
│
├── core/
│   ├── filters.py       # Hard constraint filters (pre-screening)
│   └── scorer.py        # WeightedScorer + BaseScorer interface
│
├── cli/
│   └── interface.py     # Argument parser + command handlers
│
└── data/
    ├── seed.py          # Populate DB with sample data
    └── lunchbox.db      # SQLite database (auto-created)
```

## Quickstart

```bash
# Seed sample data
python -m data.seed

# Get today's recommendations
python main.py decide

# Recommend with filters
python main.py decide --food-type noodles --max-price 15 --cooldown 7

# Specify who's joining
python main.py decide --members Zeyu --verbose

# Add a restaurant
python main.py add "Ramen House" --food-type noodles --distance 0.6 --price 14 --waiting 10 --eating 30 --rating 8

# Record a visit (with post-visit rating)
python main.py visit 3 --members Zeyu --rating 9.0 --notes "Great today!"

# List all restaurants
python main.py list
python main.py list --food-type noodles --max-price 20

# Update rating
python main.py rate 2 7.5

# Manage members
python main.py members --add "Charles" --email char@lab.com
python main.py members
```

## Restaurant Factors

| Factor           | DB Column          | Description                        |
|------------------|--------------------|------------------------------------|
| Distance         | `distance_mile`    | Walking distance from office       |
| Food type        | `food_type`        | Category (noodles, tacos, etc.)    |
| Price            | `avg_price`        | Average spend per person ($)       |
| Waiting time     | `avg_waiting_min`  | Minutes until served               |
| Eating time      | `avg_eating_min`   | Minutes to finish the meal         |
| Visited times    | `visited_times`    | Auto-incremented on each visit     |
| Last visited     | `last_visited`     | Auto-updated on each visit         |
| Internal rating  | `internal_rating`  | Group rating 1–10                  |
| Member avail.    | *(runtime input)*  | Passed via `--members` flag        |

## Scorer Weights (config.py)

```python
SCORER_WEIGHTS = {
    "distance":        0.15,
    "price":           0.15,
    "waiting_time":    0.20,
    "eating_time":     0.10,
    "internal_rating": 0.25,
    "recency_penalty": 0.15,
}
```
Edit `config.py` to tune without touching any other file.

## Upgrade Path

| Version | Planned Feature                         | Module to add/replace           |
|---------|-----------------------------------------|---------------------------------|
| v0.2    | ML-based scorer (collaborative filter)  | `core/ml_scorer.py`             |
| v0.3    | GUI / web frontend                      | `web/` (Flask or FastAPI)       |
| v0.4    | Per-member preference tracking          | `core/preference_model.py`      |
| v0.5    | Google Maps distance auto-fetch         | `services/maps_client.py`       |

To plug in a new scorer, subclass `BaseScorer` from `core/scorer.py` and pass it into `main.py`.