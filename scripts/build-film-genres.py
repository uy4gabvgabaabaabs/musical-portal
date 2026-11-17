#!/usr/bin/env python3
"""Build the portal's lightweight primary/secondary genre table."""

import csv
from pathlib import Path


PUBLIC = Path(__file__).resolve().parents[1] / "public"
FILMS_PATH = PUBLIC / "musical_portal_4409.csv"
OUTPUT_PATH = PUBLIC / "film_genres.csv"

with FILMS_PATH.open(encoding="utf-8-sig", newline="") as source:
    films = list(csv.DictReader(source))

existing: dict[str, str] = {}
if OUTPUT_PATH.exists():
    with OUTPUT_PATH.open(encoding="utf-8-sig", newline="") as source:
        existing = {row["film_id"]: row.get("genre_2", "") for row in csv.DictReader(source)}

with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=["film_id", "genre_1", "genre_2"])
    writer.writeheader()
    writer.writerows(
        {
            "film_id": film["film_id"],
            "genre_1": "موزیکال",
            "genre_2": existing.get(film["film_id"], ""),
        }
        for film in films
    )

