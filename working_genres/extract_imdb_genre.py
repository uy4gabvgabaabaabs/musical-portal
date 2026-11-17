#!/usr/bin/env python3
"""Create a review table for one IMDb genre without changing portal data."""

import argparse
import csv
import gzip
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"


parser = argparse.ArgumentParser()
parser.add_argument("genre", help="Exact IMDb genre, for example Crime")
parser.add_argument("imdb_basics", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--label", help="Display label for proposed_genre_2; defaults to IMDb genre")
parser.add_argument("--note", default="", help="Review note written to every candidate row")
args = parser.parse_args()

with FILMS.open(encoding="utf-8-sig", newline="") as source:
    films = list(csv.DictReader(source))

by_imdb = {row["imdb_id"]: row for row in films if row.get("imdb_id")}
matched: dict[str, str] = {}

with gzip.open(args.imdb_basics, "rt", encoding="utf-8", newline="") as source:
    reader = csv.DictReader(source, delimiter="\t")
    for row in reader:
        imdb_id = row["tconst"]
        if imdb_id not in by_imdb:
            continue
        genres = row.get("genres", "")
        if args.genre in genres.split(","):
            matched[imdb_id] = genres

args.output.parent.mkdir(parents=True, exist_ok=True)
fields = [
    "film_id",
    "imdb_id",
    "title",
    "persian_title",
    "year",
    "director",
    "country",
    "imdb_genres",
    "proposed_genre_2",
    "review_status",
    "review_note",
]
with args.output.open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=fields)
    writer.writeheader()
    for film in films:
        imdb_id = film.get("imdb_id", "")
        if imdb_id not in matched:
            continue
        writer.writerow(
            {
                "film_id": film["film_id"],
                "imdb_id": imdb_id,
                "title": film["title"],
                "persian_title": film["persian_title"],
                "year": film["year"],
                "director": film["director"],
                "country": film["country"],
                "imdb_genres": matched[imdb_id],
                "proposed_genre_2": args.label or args.genre,
                "review_status": "نامزد",
                "review_note": args.note,
            }
        )

print(f"films={len(films)} imdb_ids={len(by_imdb)} matched={len(matched)}")
