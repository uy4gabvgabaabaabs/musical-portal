#!/usr/bin/env python3
"""Build the custom spectacle ('عظیم') review table from Fox and Berkeley."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"
FOX_IDS = Path("/tmp/wikidata_fox_imdb.csv")
OUTPUT = ROOT / "working_genres" / "spectacle_candidates.csv"

with FILMS.open(encoding="utf-8-sig", newline="") as source:
    films = list(csv.DictReader(source))
with FOX_IDS.open(encoding="utf-8-sig", newline="") as source:
    fox_ids = {row["imdb"] for row in csv.DictReader(source)}

fields = [
    "film_id", "imdb_id", "title", "persian_title", "year", "director",
    "country", "choreographer", "classification_evidence", "proposed_genre_2",
    "review_status", "review_note",
]
with OUTPUT.open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=fields)
    writer.writeheader()
    for film in films:
        is_fox = film.get("imdb_id", "") in fox_ids
        is_berkeley = any(
            "busby berkeley" in film.get(field, "").lower()
            for field in ("director", "choreographer")
        )
        if not (is_fox or is_berkeley):
            continue
        evidence = []
        if is_fox:
            evidence.append("Fox production (Wikidata)")
        if is_berkeley:
            evidence.append("Busby Berkeley credit (portal)")
        writer.writerow({
            "film_id": film["film_id"],
            "imdb_id": film["imdb_id"],
            "title": film["title"],
            "persian_title": film["persian_title"],
            "year": film["year"],
            "director": film["director"],
            "country": film["country"],
            "choreographer": film["choreographer"],
            "classification_evidence": "; ".join(evidence),
            "proposed_genre_2": "عظیم",
            "review_status": "نامزد",
            "review_note": "تعریف عملیاتی: تولید فاکس یا اثر دارای اعتبار بازبی برکلی",
        })

