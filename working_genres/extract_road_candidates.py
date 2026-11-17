#!/usr/bin/env python3
"""Build a strict road-movie review table from Wikidata classifications."""

import csv
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"
WIKIDATA_IDS = Path("/tmp/wikidata_road_imdb.csv")
IMDB_BASICS = Path("/tmp/title.basics.tsv.gz")
OUTPUT = ROOT / "working_genres" / "road_candidates.csv"

with FILMS.open(encoding="utf-8-sig", newline="") as source:
    films = list(csv.DictReader(source))
with WIKIDATA_IDS.open(encoding="utf-8-sig", newline="") as source:
    road_ids = {row["imdb"] for row in csv.DictReader(source)}

# Clear editorial additions: canonical Road-to films and musicals structured
# around an overland journey/tour.  These compensate for sparse Wikidata tags.
editorial_ids = {
    "tt0032993", "tt0034116", "tt0035262", "tt0038032", "tt0039776",
    "tt0045094", "tt0056417",  # Road to ... series
    "tt0037297",  # Song of the Open Road
    "tt0079588",  # The Muppet Movie
    "tt0080455",  # The Blues Brothers
    "tt0113198",  # A Goofy Movie
    "tt0248845",  # Hedwig and the Angry Inch
    "tt2974918",  # Alvin and the Chipmunks: The Road Chip
    "tt2980794",  # Highway
}
road_ids |= editorial_ids

portal_ids = {row["imdb_id"] for row in films if row.get("imdb_id") in road_ids}
imdb_genres = {}
with gzip.open(IMDB_BASICS, "rt", encoding="utf-8", newline="") as source:
    for row in csv.DictReader(source, delimiter="\t"):
        if row["tconst"] in portal_ids:
            imdb_genres[row["tconst"]] = row.get("genres", "")

fields = [
    "film_id", "imdb_id", "title", "persian_title", "year", "director",
    "country", "imdb_genres", "classification_evidence", "proposed_genre_2",
    "review_status", "review_note",
]
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=fields)
    writer.writeheader()
    for film in films:
        imdb_id = film.get("imdb_id", "")
        if imdb_id not in portal_ids:
            continue
        writer.writerow({
            "film_id": film["film_id"], "imdb_id": imdb_id,
            "title": film["title"], "persian_title": film["persian_title"],
            "year": film["year"], "director": film["director"],
            "country": film["country"], "imdb_genres": imdb_genres.get(imdb_id, ""),
            "classification_evidence": (
                "بازبینی محتوایی: سفرمحور/مجموعه Road to"
                if imdb_id in editorial_ids else "Wikidata: road movie or subclass"
            ),
            "proposed_genre_2": "جاده‌ای", "review_status": "نامزد",
            "review_note": "سفر زمینی و مسیر، ساختار اصلی روایت؛ نیازمند بازبینی نهایی",
        })
