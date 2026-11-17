#!/usr/bin/env python3
"""Build a strict social-issue review table from Wikidata evidence."""

import csv
import gzip
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "public" / "musical_portal_4409.csv"
TOPICS = Path("/tmp/wikidata_social_topics.csv")
SOCIAL_GENRE = Path("/tmp/wikidata_social_imdb.csv")
IMDB_BASICS = Path("/tmp/title.basics.tsv.gz")
OUTPUT = ROOT / "working_genres" / "social_issue_candidates.csv"

ISSUE_LABELS = {
    "Q10294": "فقر",
    "Q5431887": "نابرابری اجتماعی",
    "Q8461": "نژادپرستی",
    "Q169207": "تبعیض",
    "Q131288": "مهاجرت",
    "Q41171": "بیکاری",
    "Q2915476": "حقوق کار",
    "Q223569": "حقوق زنان",
    "Q93200": "جنسیت‌زدگی",
    "Q156537": "خشونت خانگی",
    "Q3378593": "وابستگی به مواد",
    "Q15326": "الکلیسم",
    "Q131327": "بی‌خانمانی",
    "Q12131": "معلولیت",
    "Q240126": "قلدری",
    "Q1001125": "بزهکاری نوجوانان",
    "Q22649": "یهودستیزی",
    "Q33487": "همجنسگراهراسی",
    "Q12199": "ایدز",
    "Q8458": "سقط جنین",
    "Q167191": "کودک‌آزاری",
    "Q1996993": "خشونت پلیس",
    "Q841236": "زندان",
    "Q131572": "پناهندگی",
    "Q7167": "استعمار",
    "Q861360": "نابرابری آموزشی",
}

with FILMS.open(encoding="utf-8-sig", newline="") as source:
    films = list(csv.DictReader(source))

issues_by_imdb: dict[str, set[str]] = {}
with TOPICS.open(encoding="utf-8-sig", newline="") as source:
    for row in csv.DictReader(source):
        issue_id = row["issue"].rsplit("/", 1)[-1]
        issues_by_imdb.setdefault(row["imdb"], set()).add(ISSUE_LABELS[issue_id])
with SOCIAL_GENRE.open(encoding="utf-8-sig", newline="") as source:
    social_genre_ids = {row["imdb"] for row in csv.DictReader(source)}

candidate_ids = set(issues_by_imdb) | social_genre_ids
imdb_genres: dict[str, str] = {}
with gzip.open(IMDB_BASICS, "rt", encoding="utf-8", newline="") as source:
    for row in csv.DictReader(source, delimiter="\t"):
        if row["tconst"] in candidate_ids:
            imdb_genres[row["tconst"]] = row.get("genres", "")

fields = [
    "film_id", "imdb_id", "title", "persian_title", "year", "director",
    "country", "imdb_genres", "social_issues", "classification_evidence",
    "proposed_genre_2", "review_status", "review_note",
]
with OUTPUT.open("w", encoding="utf-8", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=fields)
    writer.writeheader()
    for film in films:
        imdb_id = film.get("imdb_id", "")
        if imdb_id not in candidate_ids:
            continue
        evidence = []
        if imdb_id in issues_by_imdb:
            evidence.append("Wikidata main subject")
        if imdb_id in social_genre_ids:
            evidence.append("Wikidata social problem film")
        writer.writerow({
            "film_id": film["film_id"],
            "imdb_id": imdb_id,
            "title": film["title"],
            "persian_title": film["persian_title"],
            "year": film["year"],
            "director": film["director"],
            "country": film["country"],
            "imdb_genres": imdb_genres.get(imdb_id, ""),
            "social_issues": "؛ ".join(sorted(issues_by_imdb.get(imdb_id, set()))),
            "classification_evidence": "; ".join(evidence),
            "proposed_genre_2": "اجتماعی",
            "review_status": "نامزد",
            "review_note": "معیار سخت‌گیرانه: مسئلهٔ اجتماعی محور روایت",
        })

