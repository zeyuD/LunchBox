"""
LunchBox — Entry Point
======================
Wires the database and CLI together.
Swap the scorer or add new commands here without modifying other modules.
"""

import logging
import sys

import config
from cli.interface import run_cli
from db.database import Database

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s  %(name)s  %(message)s",
)


def main() -> None:
    # ── Future hook: swap scorer here if needed ──────────────────────────────
    # from core.scorer import WeightedScorer
    # scorer = WeightedScorer(weights={...})
    # Pass scorer into CLI or inject via a service-locator pattern.

    with Database(config.DB_PATH) as db:
        db.create_all()
        run_cli(db)


if __name__ == "__main__":
    main()
