#!/usr/bin/env python3
"""Build a review table for films containing filmmaking/a film within the story."""

import csv
import gzip
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"
WIKIDATA = Path("/tmp/wikidata_filmwithin_imdb.csv")
IMDB = Path("/tmp/title.basics.tsv.gz")
OUTPUT = ROOT / "working_genres" / "film_within_film_candidates.csv"

topic_names = {
    "Q13400901": "filmmaking", "Q932586": "film production",
    "Q1415395": "film industry", "Q1306994": "story within a story",
    "Q11424": "film", "Q380675": "Hollywood / US cinema",
}
evidence = defaultdict(set)
with WIKIDATA.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        if row["imdb"].startswith("tt"):
            qid = row["topic"].rsplit("/", 1)[-1]
            evidence[row["imdb"]].add(topic_names.get(qid, qid))

# Clear editorial examples under the project's strict definition.
editorial = {
    "tt0020902",  # Free and Easy
    "tt0021371",  # Show Girl in Hollywood
    "tt0024067",  # Going Hollywood
    "tt0025263",  # Hollywood Party
    "tt0029010",  # Hollywood Hotel
    "tt0045152",  # Singin' in the Rain
    "tt0029606",  # A Star Is Born (1937)
    "tt0047522",  # A Star Is Born (1954)
    "tt0075265",  # A Star Is Born (1976)
    "tt1517451",  # A Star Is Born (2018)
    "tt0037492",  # Abbott and Costello in Hollywood
    "tt0077952",  # Movie Movie
    "tt1024943",  # Om Shanti Om
    "tt0875034",  # Nine
    "tt0114234",  # Rangeela
    "tt0886539",  # Luck by Chance
    "tt0314676",  # The Singing Detective
    "tt0404364",  # Reefer Madness: The Movie Musical
    "tt7424200",  # Teen Titans Go! To the Movies
}
editorial_film_ids = {"vault:356"}  # Kaagaz Ke Phool lacks IMDb ID in the portal

with FILMS.open(encoding="utf-8-sig", newline="") as f:
    films = list(csv.DictReader(f))
portal_ids = {r["imdb_id"] for r in films if r.get("imdb_id") in editorial}
genres = {}
with gzip.open(IMDB, "rt", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["tconst"] in portal_ids:
            genres[row["tconst"]] = row.get("genres", "")

fields = ["film_id", "imdb_id", "title", "persian_title", "year", "director", "country",
          "imdb_genres", "classification_evidence", "proposed_genre_2", "review_status", "review_note"]
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
    for film in films:
        imdb = film.get("imdb_id", "")
        if imdb not in portal_ids and film["film_id"] not in editorial_film_ids:
            continue
        ev = "; ".join(sorted(evidence.get(imdb, set()))) or "بازبینی محتوایی"
        writer.writerow({
            "film_id": film["film_id"], "imdb_id": imdb, "title": film["title"],
            "persian_title": film["persian_title"], "year": film["year"], "director": film["director"],
            "country": film["country"], "imdb_genres": genres.get(imdb, ""),
            "classification_evidence": ev, "proposed_genre_2": "فیلم در فیلم",
            "review_status": "نامزد", "review_note": "فیلم‌سازی یا فیلمِ درون روایت باید نقش مؤثر داشته باشد",
        })
