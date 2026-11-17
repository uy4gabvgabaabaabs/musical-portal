#!/usr/bin/env python3
"""Create a teen-film review table from Wikidata teen-film classifications."""

import csv
import gzip
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"
WIKIDATA_IDS = Path("/tmp/wikidata_teen_imdb.csv")
IMDB_BASICS = Path("/tmp/title.basics.tsv.gz")
OUTPUT = ROOT / "working_genres" / "teen_candidates.csv"

with FILMS.open(encoding="utf-8-sig", newline="") as source:
    films = list(csv.DictReader(source))
with WIKIDATA_IDS.open(encoding="utf-8-sig", newline="") as source:
    teen_ids = {row["imdb"] for row in csv.DictReader(source)}

portal_teen_ids = {row["imdb_id"] for row in films if row.get("imdb_id") in teen_ids}
imdb_genres: dict[str, str] = {}
with gzip.open(IMDB_BASICS, "rt", encoding="utf-8", newline="") as source:
    for row in csv.DictReader(source, delimiter="\t"):
        if row["tconst"] in portal_teen_ids:
            imdb_genres[row["tconst"]] = row.get("genres", "")

fields = [
    "film_id", "imdb_id", "title", "persian_title", "year", "director",
    "country", "imdb_genres", "classification_evidence", "proposed_genre_2",
    "review_status", "review_note",
]
with OUTPUT.open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=fields)
    writer.writeheader()
    for film in films:
        imdb_id = film.get("imdb_id", "")
        if imdb_id not in portal_teen_ids:
            continue
        writer.writerow({
            "film_id": film["film_id"],
            "imdb_id": imdb_id,
            "title": film["title"],
            "persian_title": film["persian_title"],
            "year": film["year"],
            "director": film["director"],
            "country": film["country"],
            "imdb_genres": imdb_genres.get(imdb_id, ""),
            "classification_evidence": "Wikidata: teen film or subclass",
            "proposed_genre_2": "نوجوانانه",
            "review_status": "نامزد",
            "review_note": "نیازمند بازبینی دامنهٔ نوجوانانه/بلوغ/دبیرستانی",
        })

